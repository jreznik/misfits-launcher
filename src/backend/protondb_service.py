import requests
import json
import re

class ProtonDBService:
    @staticmethod
    def get_steam_appid(title):
        """Searches Steam for the game title and returns the most likely appid."""
        try:
            # Clean title for better search
            clean_title = re.sub(r'\(.*?\)', '', title).strip()
            url = f"https://store.steampowered.com/api/storesearch/?term={clean_title}&l=english&cc=US"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('total') > 0:
                    # Return the ID of the first item
                    return str(data['items'][0].get('id'))
        except Exception as e:
            print(f"Error searching Steam AppID for {title}: {e}")
        return None

    @staticmethod
    def get_proton_summary(appid):
        """Fetches ProtonDB summary for a Steam AppID."""
        if not appid:
            return None
        try:
            url = f"https://www.protondb.com/api/v1/reports/summaries/{appid}.json"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"Error fetching ProtonDB summary for {appid}: {e}")
        return None

    @staticmethod
    def get_steam_details(appid):
        """Fetches game details from Steam, including description."""
        if not appid:
            return None
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={appid}&l=english"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get(appid, {}).get('success'):
                    return data[appid]['data']
        except Exception as e:
            print(f"Error fetching Steam details for {appid}: {e}")
        return None

    @staticmethod
    def get_game_compatibility(title):
        """Combined method to get compatibility info and Steam details by title."""
        appid = ProtonDBService.get_steam_appid(title)
        if appid:
            summary = ProtonDBService.get_proton_summary(appid)
            steam_data = ProtonDBService.get_steam_details(appid)
            if summary:
                summary['steam_appid'] = appid
                if steam_data:
                    summary['steam_description'] = steam_data.get('short_description', '')
                return summary
        return None
