import os, re
import requests, json
from datetime import date
from base64 import b64encode
from terminaltables import SingleTable
from sploitkit import Module, Config, Option
from dateutil.relativedelta import relativedelta
from pygments import highlight, lexers, formatters


class GeoWifi(Module):
    """ This module searches the information like BSSID, Location, and Encryption of the given SSID.
    https://wigle.net
    Author:  cadeath
    Version: 1.0
    """
    config = Config({
        Option(
            "WIRELESS_SSID",
            "Enter exact Wifi SSID",
            True
        ): str("PLDTHomeXXXX")
    })

    PH = {
        "Lat1":"19.2855",
        "Lat2":"5.0405",
        "Lon1":"115.8137",
        "Lon2":"126.9333"
    }
    
    def run(self):
        API_NAME = os.getenv('WIGLE_API_NAME')
        API_KEY = os.getenv('WIGLE_API_TOKEN')
        userToken = f"{API_NAME}:{API_KEY}"
        BasicAuth = b64encode(userToken.encode("utf-8"))
        BasicAuth = BasicAuth.decode("utf-8")

        WifiSSID = self.config.option('WIRELESS_SSID').value
        authHeaders = {
            'Authorization': f'Basic {BasicAuth}',
            'Accept': 'application/json',
        }


        print("Searching...")

        wifiUrl = self._requestWifiBSSID(WifiSSID)

        authHeaders = {
            'Authorization': f'Basic {BasicAuth}',
            'Accept': 'application/json',
        }

        r = requests.get(wifiUrl, headers=authHeaders)
        if r.status_code == 429:
            print("[-] Too many requests, try again later or have a new API key")
            return 

        rep = r.json()

        title = f"SSID: {WifiSSID}"
        th = ('Key','Value')
        tblDetails = [th]
        if rep["resultCount"] < 0:
            print("[-] SSID Information not found.")
            return

        th = ('Last Update','MAC','Encryption','Channel','Location', 'Coordinates')
        tblGeo = [th]
        tblGeo.extend(
            (
                el["lastupdt"],
                f"{el['netid']}",
                f"{el['encryption']}",
                f"{el['channel']}",
                f"{el['road']} {el['city']} {el['region']}, {el['country']}",
                f"{el['trilat']} , {el['trilong']}",
            )
            for el in rep["results"]
        )

        self._print(title,tblGeo)

    def _formatCheck(self,entry):
        if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", entry.lower()):
            return "MAC"
        else:
            return "SSID"

    def _print(self,title,data):        
        table = SingleTable(data,title)
        print("\n" + table.table)

    def _debug(self,jsr):
        raw_json = json.dumps(
            jsr,
            sort_keys=True,
            indent=4,
            separators=(',', ': ')
        )
        colorful = highlight(
            raw_json,
            lexer=lexers.JsonLexer(),
            formatter=formatters.TerminalFormatter(),
        )
        print(colorful)

    def _last6Mon(self):
        six_months = date.today() + relativedelta(months=-6)
        return six_months.strftime("%Y%m%d") + "000000"

    def _requestWifiBSSID(self,ssid):
        url = "https://api.wigle.net/api/v2/network/search?onlymine=false&"
        url += f"latrange1={self.PH['Lat1']}&latrange2={self.PH['Lat2']}&longrange1={self.PH['Lon1']}&longrange2={self.PH['Lon2']}"
        url += f"&lastupdt={self._last6Mon()}&freenet=false&paynet=false&country=PH"
        url += f"&ssid={ssid}"

        return url