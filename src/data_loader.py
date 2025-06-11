import requests
import os
from tqdm import tqdm

class DataLoader:
    """
    從臺北市資料大平臺下載資料，已修正 API limit 參數。
    """
    def __init__(self, dataset_id: str, limit: int = 1000):
        """
        初始化 DataLoader。

        Args:
            dataset_id (str): 資料集的 ID。
            limit (int): API 回傳的資料筆數上限。
        """
        self.dataset_id = dataset_id
        # 將 limit 參數加入 API URL 中以獲取所有資料
        self.api_url = f"https://data.taipei/api/v1/dataset/{dataset_id}?scope=resourceAquire&limit={limit}"

    def get_resource_urls(self):
        """
        從資料集 API 獲取所有資源 (CSV檔案) 的 URL 列表。
        """
        print(f"正在從 API 獲取資料集資源列表: {self.api_url}")
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            data = response.json()
            
            result_dict = data.get('result', {})
            resources_list = result_dict.get('results', [])
            
            if not resources_list:
                print("錯誤：在 API 回應中找不到資源列表。")
                return []
            
            extracted_resources = []
            for resource in resources_list:
                url = resource.get('url') or resource.get('URL')
                # 某些資源的名稱藏在'欄位說明'，有些則需自己組合
                name = resource.get('name') or f"臺北捷運OD_{resource.get('西元年')}{resource.get('月')}"

                if url and name:
                    extracted_resources.append((name, url))

            print(f"成功解析並提取到 {len(extracted_resources)} 個資源連結。")
            return extracted_resources
            
        except Exception as e:
            print(f"解析 API 回應時發生錯誤: {e}")
            return []

    def download_monthly_data(self, save_dir: str):
        """
        下載所有月度 OD 流量資料並儲存到指定目錄。
        """
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        resource_urls = self.get_resource_urls()
        if not resource_urls:
            print("沒有可下載的檔案，程序終止。")
            return

        print(f"\n準備開始下載 {len(resource_urls)} 個檔案至 '{save_dir}'...")
        
        for name, url in tqdm(resource_urls, desc="下載進度"):
            try:
                # 從名稱中提取可能的年月資訊作為檔名
                year_month_part = name.split('_')[-1]
                if year_month_part.isdigit() and len(year_month_part) == 6:
                    filename = f"{year_month_part}.csv"
                else: # 如果格式不符，使用清理過的原始名稱
                    safe_name = "".join(c for c in name if c.isalnum() or c in ('_', '-')).rstrip()
                    filename = f"{safe_name}.csv"
                
                filepath = os.path.join(save_dir, filename)

                if os.path.exists(filepath):
                    continue

                res = requests.get(url, stream=True)
                res.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            except requests.exceptions.RequestException as e:
                print(f"下載失敗 (URL: {url}): {e}")
            except Exception as e:
                print(f"處理檔案時發生錯誤 (名稱: {name}): {e}")
        
        print("\n所有檔案下載完成。")