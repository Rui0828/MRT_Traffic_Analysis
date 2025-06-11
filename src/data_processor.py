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
    csv_files = glob.glob(os.path.join(raw_data_dir, '*.csv'))
    
    if not csv_files:
        print(f"警告：在 '{raw_data_dir}' 中找不到任何 CSV 檔案。")
        return pd.DataFrame()
        
    print(f"找到 {len(csv_files)} 個 CSV 檔案，準備讀取與合併...")
    
    df_list = []
    for file_path in tqdm(sorted(csv_files), desc="正在讀取檔案"):
        try:
            df = pd.read_csv(file_path)
            df_list.append(df)
        except Exception as e:
            print(f"讀取檔案 '{os.path.basename(file_path)}' 時發生錯誤: {e}")
            
    if not df_list:
        print("錯誤：沒有任何檔案成功讀取。")
        return pd.DataFrame()

    print("\n正在合併所有資料...")
    full_df = pd.concat(df_list, ignore_index=True)
    print("所有資料已成功合併！")
    
    return full_df

def process_and_aggregate_data(df: pd.DataFrame, target_station: str) -> pd.DataFrame:
    """
    對合併後的 DataFrame 進行清理、轉換與彙總。

    Args:
        df (pd.DataFrame): 合併後的原始 DataFrame。
        target_station (str): 要分析的目標捷運站名，例如 '臺北車站'。

    Returns:
        pd.DataFrame: 以時間為索引，包含目標站點進出站人次的彙總後 DataFrame。
    """
    print("=== 開始資料清理與轉換 ===")
    
    # 1. 建立標準時間戳 (Timestamp)
    print("步驟 1/4: 建立標準時間戳...")
    # 將 '時段' 補零成兩位數，例如 8 -> '08'
    df['時段_str'] = df['時段'].astype(str).str.zfill(2)
    # 合併成 'YYYY-MM-DD HH:00:00' 格式的字串
    datetime_str = df['日期'] + ' ' + df['時段_str'] + ':00:00'
    # 轉換為 datetime 物件，並將錯誤的轉換設為 NaT (Not a Time)
    df['時間戳'] = pd.to_datetime(datetime_str, errors='coerce')
    # 移除處理過程中的輔助欄位
    df = df.drop(columns=['日期', '時段', '時段_str'])
    # 移除時間戳轉換失敗的行
    df = df.dropna(subset=['時間戳'])
    
    # 2. 優化記憶體使用
    print("步驟 2/4: 優化記憶體使用...")
    # 將站名轉為 category 型別，可大幅減少記憶體佔用
    df['進站'] = df['進站'].astype('category')
    df['出站'] = df['出站'].astype('category')
    # 將人次從 64 位元整數降為 32 位元，因為人次數值用不到那麼大
    df['人次'] = df['人次'].astype('int32')
    
    print("--- 清理後 DataFrame 的基本資訊 ---")
    df.info()

    # 3. 彙總資料到站點層級
    print(f"\n步驟 3/4: 彙總 '{target_station}' 的進出站資料...")
    # 計算每個站在每個小時的總進站人次
    df_entries = df.groupby(['時間戳', '進站'])['人次'].sum().rename('進站人次')
    # 計算每個站在每個小時的總出站人次
    df_exits = df.groupby(['時間戳', '出站'])['人次'].sum().rename('出站人次')
    
    # 篩選出目標站點的資料
    station_entries = df_entries.loc[(slice(None), target_station),].reset_index(level='進站', drop=True)
    station_exits = df_exits.loc[(slice(None), target_station),].reset_index(level='出站', drop=True)
    
    # 4. 合併進站與出站資料
    print(f"步驟 4/4: 合併 '{target_station}' 的進站與出站資料...")
    # 使用 pd.concat 將兩個 Series 合併成一個 DataFrame，並用 0 填充缺失值
    station_df = pd.concat([station_entries, station_exits], axis=1).fillna(0)
    
    # 將欄位轉為整數
    station_df['進站人次'] = station_df['進站人次'].astype(int)
    station_df['出站人次'] = station_df['出站人次'].astype(int)
    
    # 計算總人次
    station_df['總人次'] = station_df['進站人次'] + station_df['出站人次']

    print(f"\n=== '{target_station}' 資料彙總完成！ ===")
    
    return station_df