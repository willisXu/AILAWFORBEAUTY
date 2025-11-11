"""
Update Checker Module
更新檢查模組 - 檢查法規文件更新
"""

import re
import requests
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from bs4 import BeautifulSoup


class UpdateChecker:
    """法規更新檢查器"""

    def __init__(self):
        self.update_sources = {
            'EU': 'https://ec.europa.eu/growth/tools-databases/cosing/',
            'NMPA': 'https://www.nmpa.gov.cn/',
            'ASEAN': 'https://hpfb-dgpsa.github.io/ASEAN-Cosmetics/'
        }

    def check_eu_cosing_update(self) -> Dict:
        """
        檢查 EU COSING 更新

        Returns:
            更新資訊字典
        """
        result = {
            'region': 'EU',
            'source': 'COSING',
            'status': 'unknown',
            'latest_version': None,
            'update_date': None,
            'message': ''
        }

        try:
            url = self.update_sources['EU']
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # 查找更新日期資訊
                # 注意: 實際實作需要根據網站結構調整
                date_pattern = r'Last update[d]?:?\s*(\d{2}/\d{2}/\d{4})'
                matches = re.findall(date_pattern, response.text, re.IGNORECASE)

                if matches:
                    result['update_date'] = matches[0]
                    result['status'] = 'available'
                    result['message'] = f'Latest update found: {matches[0]}'
                else:
                    result['status'] = 'no_info'
                    result['message'] = 'Cannot find update information'

            else:
                result['status'] = 'error'
                result['message'] = f'HTTP {response.status_code}'

        except Exception as e:
            result['status'] = 'error'
            result['message'] = str(e)

        return result

    def check_china_nmpa_update(self) -> Dict:
        """
        檢查中國 NMPA 更新

        Returns:
            更新資訊字典
        """
        result = {
            'region': 'China',
            'source': 'NMPA',
            'status': 'unknown',
            'latest_announcement': None,
            'update_date': None,
            'message': ''
        }

        try:
            url = self.update_sources['NMPA']
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0'
            })

            if response.status_code == 200:
                # 簡化版本 - 實際需要根據 NMPA 網站結構解析
                result['status'] = 'check_manually'
                result['message'] = 'Please check NMPA website manually for updates'

            else:
                result['status'] = 'error'
                result['message'] = f'HTTP {response.status_code}'

        except Exception as e:
            result['status'] = 'error'
            result['message'] = str(e)

        return result

    def check_asean_update(self) -> Dict:
        """
        檢查 ASEAN 更新

        Returns:
            更新資訊字典
        """
        result = {
            'region': 'ASEAN',
            'source': 'ASEAN Cosmetic Directive',
            'status': 'unknown',
            'latest_version': None,
            'update_date': None,
            'message': ''
        }

        try:
            url = self.update_sources['ASEAN']
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                # 查找版本資訊
                version_pattern = r'Version\s*(\d{4}-\d+)'
                matches = re.findall(version_pattern, response.text, re.IGNORECASE)

                if matches:
                    result['latest_version'] = matches[0]
                    result['status'] = 'available'
                    result['message'] = f'Latest version found: {matches[0]}'
                else:
                    result['status'] = 'no_info'
                    result['message'] = 'Cannot find version information'

            else:
                result['status'] = 'error'
                result['message'] = f'HTTP {response.status_code}'

        except Exception as e:
            result['status'] = 'error'
            result['message'] = str(e)

        return result

    def check_all_updates(self) -> Dict[str, Dict]:
        """
        檢查所有地區的更新

        Returns:
            所有地區的更新資訊
        """
        print("Checking for regulation updates...")
        print("-" * 80)

        results = {}

        # EU
        print("Checking EU COSING...")
        results['EU'] = self.check_eu_cosing_update()
        print(f"Status: {results['EU']['status']} - {results['EU']['message']}\n")

        # China
        print("Checking China NMPA...")
        results['China'] = self.check_china_nmpa_update()
        print(f"Status: {results['China']['status']} - {results['China']['message']}\n")

        # ASEAN
        print("Checking ASEAN...")
        results['ASEAN'] = self.check_asean_update()
        print(f"Status: {results['ASEAN']['status']} - {results['ASEAN']['message']}\n")

        print("-" * 80)

        return results

    def compare_local_version(self, local_file: Path, region: str) -> Dict:
        """
        比對本地文件版本

        Args:
            local_file: 本地文件路徑
            region: 地區名稱

        Returns:
            比對結果
        """
        result = {
            'file': local_file.name,
            'exists': local_file.exists(),
            'modified_date': None,
            'needs_update': None
        }

        if local_file.exists():
            # 取得文件修改時間
            modified_timestamp = local_file.stat().st_mtime
            modified_date = datetime.fromtimestamp(modified_timestamp)
            result['modified_date'] = modified_date.strftime('%Y-%m-%d %H:%M:%S')

            # 建議檢查更新 (超過 30 天)
            days_old = (datetime.now() - modified_date).days
            result['days_old'] = days_old
            result['needs_update'] = days_old > 30

        return result


class VersionTracker:
    """版本追蹤器"""

    def __init__(self, version_file: Path):
        """
        初始化版本追蹤器

        Args:
            version_file: 版本記錄文件路徑
        """
        self.version_file = Path(version_file)
        self.versions = self._load_versions()

    def _load_versions(self) -> Dict:
        """載入版本記錄"""
        if self.version_file.exists():
            import json
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_version(self, region: str, version: str, date: str):
        """
        保存版本資訊

        Args:
            region: 地區
            version: 版本號
            date: 日期
        """
        if region not in self.versions:
            self.versions[region] = []

        self.versions[region].append({
            'version': version,
            'date': date,
            'recorded_at': datetime.now().isoformat()
        })

        self._save_versions()

    def _save_versions(self):
        """保存版本記錄"""
        import json
        self.version_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(self.versions, f, ensure_ascii=False, indent=2)

    def get_latest_version(self, region: str) -> Optional[Dict]:
        """
        取得最新版本

        Args:
            region: 地區

        Returns:
            版本資訊字典或 None
        """
        if region in self.versions and self.versions[region]:
            return self.versions[region][-1]
        return None

    def get_version_history(self, region: str) -> list:
        """
        取得版本歷史

        Args:
            region: 地區

        Returns:
            版本歷史列表
        """
        return self.versions.get(region, [])
