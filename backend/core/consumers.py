import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from .models import Client, InvoiceLedger

logger = logging.getLogger(__name__)

class TallyAgentSyncConsumer(AsyncWebsocketConsumer):
    """
    Handles the persistent WebSocket connection from the local desktop Tally agent.
    Routes approved cloud invoices down to the local machine and catches Tally XML confirmations.
    """

    async def connect(self):
        # Secure connection authorization via headers or query string
        # Expected header: X-Agent-Key
        
        # For Channels, custom headers are accessible via self.scope['headers']
        headers = dict(self.scope['headers'])
        agent_key = headers.get(b'x-agent-key', b'').decode('utf-8')
        
        # If not in headers, try subprotocols for browser testing support
        subprotocols = self.scope.get('subprotocols', [])
        accepted_subprotocol = None
        
        if not agent_key:
            if 'x-agent-key' in subprotocols:
                try:
                    idx = subprotocols.index('x-agent-key')
                    if idx + 1 < len(subprotocols):
                        agent_key = subprotocols[idx + 1]
                        accepted_subprotocol = 'x-agent-key'
                except ValueError:
                    pass
            elif len(subprotocols) > 0:
                agent_key = subprotocols[0]
                accepted_subprotocol = subprotocols[0]
        else:
            if b'x-agent-key' in headers:
                accepted_subprotocol = 'x-agent-key'

        if not agent_key:
            # Reject connection if no key
            await self.close(code=4001)
            return

        # Authenticate token against Client records
        self.client_obj = await self.authenticate_agent(agent_key)
        
        if not self.client_obj:
            await self.close(code=4003)
            return

        # Add to client-specific routing group
        self.room_group_name = f"tally_sync_client_{self.client_obj.id}"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Browsers require echoing back one of the requested subprotocols to complete handshake
        await self.accept(subprotocol=accepted_subprotocol)
        logger.info(f"Tally Agent connected for Client: {self.client_obj.id}")

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        logger.info(f"Tally Agent disconnected (code {close_code})")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Catches the Tally confirmation signature callback after the agent
        successfully posts the XML to the local Tally instance.
        """
        try:
            payload = json.loads(text_data)
            action = payload.get('action')

            if action == 'INVOICE_SYNC_SUCCESS':
                invoice_id = payload.get('invoice_id')
                tally_reference = payload.get('tally_master_id')
                
                # Update the primary ledger status in the database
                await self.mark_invoice_synced(invoice_id, tally_reference)
                
                # Acknowledge back to the agent
                await self.send(text_data=json.dumps({
                    'status': 'ACK',
                    'invoice_id': invoice_id
                }))

        except json.JSONDecodeError:
            logger.error("Invalid JSON received from Tally agent")
        except Exception as e:
            logger.error(f"Error handling agent message: {e}")

    # Custom event handler called by channel_layer.group_send from backend views/tasks
    async def push_invoice_to_tally(self, event):
        """
        When the web frontend approves an invoice, this is called to format 
        an XML payload and route it down the open socket to the local machine.
        """
        invoice_data = event['invoice_data']
        
        # The agent expects a specific JSON envelope to convert to Tally XML locally
        agent_payload = {
            'action': 'POST_SALES_VOUCHER',  # or POST_PURCHASE_VOUCHER depending on context
            'payload': invoice_data
        }
        
        await self.send(text_data=json.dumps(agent_payload))

    @database_sync_to_async
    def authenticate_agent(self, token):
        """
        Verifies the X-Agent-Key corresponds to a valid, active Client.
        In production, use a dedicated secure Token model rather than a direct field.
        """
        try:
            # Assuming 'phone_number' acts as the token for this skeletal demo.
            # In a real app, this would be a secure `tally_sync_token` field on the Client model.
            return Client.objects.get(phone_number=token, is_active=True)
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def mark_invoice_synced(self, invoice_id, tally_reference):
        """
        Updates the invoice status to APPROVED (or SYNCED_TO_ERP) once Tally confirms.
        """
        try:
            invoice = InvoiceLedger.objects.get(id=invoice_id)
            invoice.processing_status = InvoiceLedger.ProcessingStatus.APPROVED
            # Add tally_reference to a JSON metadata field or dedicated field if it existed
            invoice.save(update_fields=['processing_status'])
        except InvoiceLedger.DoesNotExist:
            pass
