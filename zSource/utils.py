import requests
import zipfile
import plistlib
import github
import pandas as pd
import os
import shutil


def get_first_digit_index(string):
    for i, c in enumerate(string):
        if c.isdigit():
            return i
    return -1


def get_single_bundle_id(url, name="temp.ipa"):
    reponse = requests.get(url)
    open(name, 'wb').write(reponse.content)

    icon_folder = "icons/"
    if not os.path.exists(icon_folder):
        os.mkdir(icon_folder)

    with zipfile.ZipFile(name, mode="r") as archive:
        for file_name in archive.namelist():
            if file_name.endswith(".app/Info.plist"):
                info_file = file_name
                folder_path = os.path.dirname(info_file)

        with archive.open(info_file) as fp:
            pl = plistlib.load(fp)
            icon_path = ""
            bundleId = pl["CFBundleIdentifier"]
            if "CFBundleIconFiles" in pl.keys():
                try:
                    icon_path = os.path.join(
                        folder_path, pl["CFBundleIconFiles"][0])
                except:
                    # index [0] out-of-range: empty icon list
                    return bundleId
            if "CFBundleIcons" in pl.keys():
                try:
                    icon_prefix = pl["CFBundleIcons"]["CFBundlePrimaryIcon"]["CFBundleIconFiles"][0]
                except:
                    icon_prefix = pl["CFBundleIcons"]["CFBundlePrimaryIcon"]["CFBundleIconName"]
                for file_name in archive.namelist():
                    if icon_prefix in file_name and "__MACOSX" not in file_name:
                        icon_path = file_name
            if icon_path:
                try:
                    with archive.open(icon_path) as origin, open(icon_folder + bundleId + ".png", "wb") as dst:
                        shutil.copyfileobj(origin, dst)
                except:
                    pass
            else:  # no icon info
                pass

            return bundleId

    return "com.example.app"


def generate_bundle_id_csv(token=None):
    g = github.Github(token)
    repo = g.get_repo("purp0s3/Tweaked-iOS-Apps")
    releases = repo.get_releases()

    df = pd.DataFrame(columns=["name", "bundleId"])

    for release in releases:
        print(release.title)
        for asset in release.get_assets():
            if (asset.name[-4:] != ".ipa"):
                continue
            name = asset.name[:-4]

            try:
                app_name = name.split("_", 1)[0]
                app_name = app_name[:get_first_digit_index(app_name)]
            except:
                app_name = name

            if app_name in df.name.values:
                continue
            df = pd.concat(
                [
                    df,
                    pd.DataFrame(
                        {
                            "name": [app_name],
                            "bundleId": get_single_bundle_id(asset.browser_download_url)
                        }
                    )
                ],
                ignore_index=True
            )

    df.to_csv("bundleId.csv", index=False)


if __name__ == "__main__":
    generate_bundle_id_csv()
