import shutil
from utils import get_cache_dirs


def remove_cache_dirs():
    for cache in get_cache_dirs():
        shutil.rmtree(cache)


if __name__ == "__main__":
    remove_cache_dirs()
