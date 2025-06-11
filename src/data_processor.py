import pandas as pd
import os
import glob
from tqdm import tqdm

def load_and_merge_raw_data(raw_data_dir: str) -> pd.DataFrame:
    """
    讀取指定目錄下所有的 CSV 檔案，並將它們合併成一個 pandas DataFrame。

    Args:
        raw_data_dir (str): 存放原始 CSV 檔案的目錄路徑。

    Returns:
        pd.DataFrame: 一個包含所有月份資料的合併後 DataFrame。
                      如果目錄不存在或沒有CSV檔案，則返回一個空的 DataFrame。
    """
    # 使用 glob 尋找所有 .csv 檔案的路徑
    csv_files = glob.glob(os.path.join(raw_data_dir, '*.csv'))
    
    if not csv_files:
        print(f"警告：在 '{raw_data_dir}' 中找不到任何 CSV 檔案。")
        return pd.DataFrame()
        
    print(f"找到 {len(csv_files)} 個 CSV 檔案，準備讀取與合併...")
    
    df_list = []
    for file_path in tqdm(sorted(csv_files), desc="正在讀取檔案"):
        try:
            # 讀取單一 CSV 檔案
            df = pd.read_csv(file_path)
            df_list.append(df)
        except Exception as e:
            print(f"讀取檔案 '{os.path.basename(file_path)}' 時發生錯誤: {e}")
            
    if not df_list:
        print("錯誤：沒有任何檔案成功讀取。")
        return pd.DataFrame()

    # 使用 concat 將所有 DataFrame 合併起來
    print("\n正在合併所有資料...")
    full_df = pd.concat(df_list, ignore_index=True)
    print("所有資料已成功合併！")
    
    return full_df