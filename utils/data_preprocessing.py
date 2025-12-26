import pandas as pd
import os
import glob

import warnings


class DATA():
    def prepare_data(folder='../data/source/temp',
                     out_file='../data/processed/25-11-2025_01-12-2025.xlsx') -> pd.DataFrame():
        if not os.path.isdir(folder):
            raise ValueError(f"Folder '{folder}' does not exist or is not a directory")

        files = glob.glob(os.path.join(folder, '*.csv'))

        if not files:
            warnings.warn(f"No CSV files found in folder: {folder}")
            return pd.DataFrame()

        print(f"Found {len(files)} CSV files in folder: {folder}")

        list_of_dfs = []
        for f in files:
            df = pd.read_csv(f)
            list_of_dfs.append(df)
        df = pd.concat(list_of_dfs, ignore_index=True)
        df.to_excel(out_file)
        return df


    def pivot_metrics() -> pd.DataFrame():
        pass


if __name__ == '__main__':
    # Создаем объект класса DATA для подготовки данных для работы из исходников
    data = DATA()

    # 1. Готовим данные значений метрик выгруженные по 20 серверам за период: с 25-11-2025 по 01-12-2025
    # Папка с данными data/temp собранный датафрейм сохраняется в файл 25-11-2025_01-12-2025.xlsx
    df = data.prepare_data(folder='../data/source/temp', out_file='../data/processed/25-11-2025_01-12-2025.xlsx')

    # 2. Далее создаем сводную таблицу по этим серверам и метрикам
    df_wide = data.pivot_metrics()

    # 3. Готовим данные по

