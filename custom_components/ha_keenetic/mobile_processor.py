from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp
from homeassistant.helpers.update_coordinator import UpdateFailed

@dataclass
class MobileMetrics:
    operator: Optional[str]
    state: Optional[str]           # connection-state/state/link
    technology: Optional[str]      # "mobile" (4G/3G/…)
    rssi: Optional[str]
    rsrp: Optional[str]
    rsrq: Optional[str]
    sinr: Optional[str]            # 'cinr' alanı
    band: Optional[str]
    cell_id: Optional[str]         # 'phy-cell-id'
    tac: Optional[str]             # LAC/TAC
    raw: Dict[str, Any]

@dataclass
class MobileConfig:
    roaming: Optional[bool]
    pdp: Optional[str]
    mtu: Optional[str]
    up: Optional[bool]
    raw: Dict[str, Any]

class MobileProcessor:
    """
    Keenetic RCI Mobile Processor
    - Durum: POST /rci/  body={"show":{"interface":{"name": <iface> }}}
    - Konfig: GET  /rci/interface/<iface>
    - SMS:    POST /rci/  body=[{"sms":{"send":{"interface":<iface>, "to":..., "message":...}}}]
    """

    def __init__(self, host: str, username: str, password: str, verify_ssl: bool = False, interface: str = "UsbLte0"):
        self._interface = interface
        self._verify_ssl = verify_ssl
        if host.startswith("http://") or host.startswith("https://"):
            self._base = host.rstrip("/")
        else:
            self._base = f"http://{host}"
        self._auth = aiohttp.BasicAuth(username, password)

    @property
    def interface(self) -> str:
        return self._interface

    async def fetch_status(self, session: aiohttp.ClientSession) -> MobileMetrics:
        url = f"{self._base}/rci/"
        body = {"show": {"interface": {"name": self._interface}}}
        async with session.post(url, json=body, auth=self._auth, ssl=self._verify_ssl) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise UpdateFailed(f"RCI status HTTP {resp.status}: {text[:200]}")
            data = await resp.json(content_type=None)

        iface = (data or {}).get("show", {}).get("interface", {}) or {}
        return MobileMetrics(
            operator = iface.get("operator"),
            state = iface.get("connection-state") or iface.get("state") or iface.get("link"),
            technology = iface.get("mobile"),
            rssi = iface.get("rssi"),
            rsrp = iface.get("rsrp"),
            rsrq = iface.get("rsrq"),
            sinr = iface.get("cinr"),
            band = iface.get("band"),
            cell_id = iface.get("phy-cell-id"),
            tac = iface.get("tac"),
            raw = iface,
        )

    async def fetch_config(self, session: aiohttp.ClientSession) -> MobileConfig:
        # Senin verdiğin konfig JSON burada dönüyor
        url = f"{self._base}/rci/interface/{self._interface}"
        async with session.get(url, auth=self._auth, ssl=self._verify_ssl) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise UpdateFailed(f"RCI config HTTP {resp.status}: {text[:200]}")
            data = await resp.json(content_type=None)

        mobile = (data or {}).get("mobile", {}) or {}
        ip = (data or {}).get("ip", {}) or {}
        return MobileConfig(
            roaming = mobile.get("roaming"),
            pdp = mobile.get("pdp"),
            mtu = ip.get("mtu"),
            up = data.get("up"),
            raw = data or {},
        )

    async def send_sms(self, session: aiohttp.ClientSession, to: str, message: str) -> Dict[str, Any]:
        url = f"{self._base}/rci/"
        body = [{"sms": {"send": {"interface": self._interface, "to": to, "message": message}}}]
        async with session.post(url, json=body, auth=self._auth, ssl=self._verify_ssl) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise UpdateFailed(f"RCI SMS HTTP {resp.status}: {text[:200]}")
            return await resp.json(content_type=None)
