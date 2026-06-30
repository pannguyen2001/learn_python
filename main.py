import os
from dotenv import load_dotenv

load_dotenv()
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
KAGGLE_KEY = os.getenv("KAGGLE_KEY")

from helpers.strategy.download.google_driver_downloader import GoogleDriverDownloader
from helpers.strategy.download.kaggle_dowloader import KaggleDownloader
from helpers.strategy.download.hugging_face_downloader import HuggingFaceDownloader

# GoogleDriverDownloader(
#     id="14vCUXklVCUN_rCPKYN7ys2tDJG72SNYw",
#     path="/home/user/datacrawling/data/raw/2026-05-12/test_data",
#     item_type="folder",
#     quiet=False,
# ).execute()


# KaggleDownloader(
#     id="muratkokludataset/acoustic-extinguisher-fire-dataset",
#     path="/home/user/datacrawling/data/raw/2026-05-12/test_data",
#     unzip=True,
# ).execute()


HuggingFaceDownloader(
    url="",
    id="tmquan/sapnhap-bando-vn",
    path="/home/user/datacrawling/data/raw/2026-05-12/sapnhap-bando-vn.parquet",
    file_name="data/all.parquet",
).execute()
