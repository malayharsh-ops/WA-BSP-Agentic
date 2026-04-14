"""
Salesforce integration — optional.
Creates/updates Opportunities when a lead is handed off and resolved.
"""

import logging
from app.config import settings

logger = logging.getLogger(__name__)


class SalesforceClient:
    def __init__(self):
        self._sf = None

    def _get_client(self):
        if not settings.salesforce_enabled:
            return None
        if self._sf is None:
            try:
                from simple_salesforce import Salesforce
                self._sf = Salesforce(
                    instance_url=settings.salesforce_instance_url,
                    client_id=settings.salesforce_client_id,
                    client_secret=settings.salesforce_client_secret,
                    # Username/password flow not used; relies on OAuth2 connected app
                )
            except Exception as e:
                logger.error(f"Salesforce init failed: {e}")
                return None
        return self._sf

    def upsert_opportunity(self, lead_data: dict) -> str | None:
        """
        Upsert a Salesforce Opportunity from lead data.
        Returns the SF Opportunity ID or None.
        """
        sf = self._get_client()
        if sf is None:
            return None

        try:
            result = sf.Opportunity.upsert(
                f"JSW_WA_Phone__c/{lead_data['phone']}",
                {
                    "Name": f"WA Lead - {lead_data.get('name', lead_data['phone'])}",
                    "StageName": "Prospecting",
                    "CloseDate": "2099-12-31",
                    "LeadSource": "WhatsApp",
                    "Description": (
                        f"Qualification Score: {lead_data.get('score', 0)}\n"
                        f"Project: {lead_data.get('project_type', '')} in {lead_data.get('project_location', '')}\n"
                        f"Material: {lead_data.get('material_needed', '')}\n"
                        f"Volume: {lead_data.get('volume_mt', '')} MT\n"
                        f"Conversation ID: {lead_data.get('conversation_id', '')}"
                    ),
                    "JSW_WA_Conversation_ID__c": lead_data.get("conversation_id", ""),
                    "JSW_WA_Score__c": lead_data.get("score", 0),
                    "JSW_WA_Phone__c": lead_data["phone"],
                },
            )
            logger.info(f"SF upsert result: {result}")
            return result.get("id")
        except Exception as e:
            logger.error(f"SF upsert failed for {lead_data.get('phone')}: {e}")
            return None


sf_client = SalesforceClient()
