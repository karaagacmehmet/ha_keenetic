"""Mobile data processor for Keenetic integration. For now integrated modem."""
import json
import aiohttp
import logging
from typing import Dict, Any

_LOGGER = logging.getLogger(__name__)


_TURKISH_ENCODINGS = ("utf-8", "iso-8859-9", "windows-1254", "latin-1")


async def _safe_json_from_response(resp: aiohttp.ClientResponse):
        """
        JSON'ı güvenli biçimde yükle:
        1) resp.json(content_type=None)  -> Content-Type yanlış olsa da dener
        2) ham bayttan çeşitli encoding kombinasyonlarıyla decode + json.loads
        """
        # 1) En doğru ve hızlı yol
        try:
            return await resp.json(content_type=None)
        except Exception as e1:
            _LOGGER.debug("resp.json() failed: %s; trying byte-decoding fallbacks", e1)

        # 2) Ham baytları al
        raw = await resp.read()

        # A: JSON 'bytes' ise doğrudan json.loads kabul etmez, decode gerekir
        last_err = None
        for enc in _TURKISH_ENCODINGS:
            try:
                text = raw.decode(enc)
                return json.loads(text)
            except Exception as e2:
                last_err = e2
                continue

        # B: Son çare: hatalı karakterleri atla (json bozulabilir; bu yüzden sadece debug amaçlı)
        try:
            text = raw.decode("utf-8", errors="ignore")
            return json.loads(text)
        except Exception:
            pass

        # Pes: Hata ver, kısa bir önizleme ekle
        snippet = raw[:200].hex()
        raise ValueError(
            f"Failed to parse JSON with common encodings. Last error: {last_err}; "
            f"first-bytes={snippet}"
        )

class MobileProcessor:
    """Process Mobile data from Keenetic router."""

    @staticmethod
    async def process_interfaces(session, base_url, auth_token) -> Dict[str, Any]:
        """Process Mobile interfaces and return formatted data."""
        mobile_data = {}
        # try:
        #     for band in ["UsbLte0"]:
        #         async with session.get(
        #             f"{base_url}/rci/interface/{band}",
        #             headers={"Authorization": f"Basic {auth_token}"},
        #         ) as response:
        #             if response.status == 200:
        #                 master_data = await response.json()
        #                 _LOGGER.warning("%s data: %s", band, master_data)
                        
        #                 ap_id = band

        #                 mobile_data[ap_id] = {
        #                     "id": ap_id,
        #                     "type": "mobile",
        #                     "description": master_data.get("description", ""),
        #                     "mobile": master_data.get("mobile"),
        #                     "up": master_data.get("up", False),
        #                     "link": "up" if master_data.get("up") else "down",
        #                 }

                                        
        #     _LOGGER.warning("Processed Mobile interfaces: %s", mobile_data)
        #     return mobile_data
            
        # except Exception as ex:
        #     _LOGGER.error("Error processing Mobile interfaces: %s", str(ex))
        #     return {}

        try:
            for band in ["UsbLte0"]:
                async with session.post(
                    f"{base_url}/rci/",
                    headers={"Authorization": f"Basic {auth_token}"},
                    json={"show": {"interface": {"name": band}}}
                ) as response:
                    if response.status == 200:
                        
                        data  = await _safe_json_from_response(response)
                   
                        master_data = (data or {}).get("show", {}).get("interface", {}) or {}
                        _LOGGER.debug("%s master data: %s", band, master_data)
                        
                        ap_id = band

                        mobile_data[ap_id] = {
                            "id": ap_id,
                            "type": master_data.get("type",0),
                            "interface-name": master_data.get("interface-name", ""),
                            "mac": master_data.get("mac", ""),
                            "mobile": master_data.get("mobile", ""),
                            "operator": master_data.get("operator", ""),
                            "connected" : master_data.get("connected",""),
                            "connection-state" : master_data.get("connection-state",""),
                            "state" : master_data.get("state",""),
                            "description": master_data.get("description", ""),
                            "sim": master_data.get("sim"),
                            "up": True if  master_data.get("connected") == "yes" else False,
                            "link": master_data.get("link"),
                            "temperature": master_data.get("temperature"),
                        }

                                        
            _LOGGER.debug("Processed Mobile interfaces: %s", mobile_data)
            return mobile_data
            
        except Exception as ex:
            _LOGGER.error("Error processing Mobile interfaces: %s", str(ex))
            return {}