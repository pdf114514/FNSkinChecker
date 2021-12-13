from PIL import Image
import aiohttp
import asyncio
import re
from os import path
import io

#Epic Games#
launcher_token="MzQ0NmNkNzI2OTRjNGE0NDg1ZDgxYjc3YWRiYjIxNDE6OTIwOWQ0YTVlMjVhNDU3ZmI5YjA3NDg5ZDMxM2I0MWE="
idpattern = re.compile("athena(.*?):(.*?)_(.*?)")

async def authorize(auth_code: str, session: aiohttp.ClientSession) -> dict:    
    async with session.post(
        "https://account-public-service-prod03.ol.epicgames.com/account/api/oauth/token",
        headers={
            "Authorization":f"basic {launcher_token}"
        },
        data={
            "grant_type":"authorization_code",
            "code":auth_code,
            "token":"eg1"
        }
    ) as resp:
        print(await resp.text())
        if resp.status != 200:
            #print(f"Invalid Status Code {response.status_code}\n{response.text}")
            return f"Error ({resp.status})"
        else:
            return await resp.json()

async def grabprofile(info: dict, profileid: str = "athena", session: aiohttp.ClientSession = False) -> dict:
    async with session.post(
        f"https://fortnite-public-service-prod11.ol.epicgames.com/fortnite/api/game/v2/profile/{info['account_id']}/client/QueryProfile?profileId={profileid}",
        headers={
            "Authorization": f"bearer {info['access_token']}",
            "content-type": "application/json"
        },
        json={}
    ) as resp:
        print((await resp.text())[:500])
        if resp.status != 200:
            return f"Error ({resp.status})"
        else:
            return await resp.json()

#Image#
def get_concat_h_multi_resize(im_list, resample=Image.BICUBIC):
    min_height = min(im.height for im in im_list)
    im_list_resize = [im.resize((int(im.width * min_height / im.height), min_height),resample=resample)
                      for im in im_list]
    total_width = sum(im.width for im in im_list_resize)
    dst = Image.new('RGB', (total_width, min_height))
    pos_x = 0
    for im in im_list_resize:
        dst.paste(im, (pos_x, 0))
        pos_x += im.width
    return dst

def get_concat_v_multi_resize(im_list, resample=Image.BICUBIC):
    min_width = min(im.width for im in im_list)
    im_list_resize = [im.resize((min_width, int(im.height * min_width / im.width)),resample=resample)
                      for im in im_list]
    total_height = sum(im.height for im in im_list_resize)
    dst = Image.new('RGB', (min_width, total_height))
    pos_y = 0
    for im in im_list_resize:
        dst.paste(im, (0, pos_y))
        pos_y += im.height
    return dst

def get_concat_tile_resize(im_list_2d, resample=Image.BICUBIC):
    im_list_v = [get_concat_h_multi_resize(im_list_h, resample=resample) for im_list_h in im_list_2d]
    return get_concat_v_multi_resize(im_list_v, resample=resample)

async def createimg(ids: list, lengthperline: int = -1, footertext: str = "https://sc.xthe.org/", session: aiohttp.ClientSession = False) -> bytes:
    async def _dl(id: str):
        imgpath = f"./cache/{id}.png"
        if not path.exists(imgpath) or not path.isfile(imgpath):
            async with session.get(f"https://fortnite-api.com/images/cosmetics/br/{id}/smallicon.png") as resp:
                print(resp.status, id)
                open(f"./cache/{id}.png", "wb").write(await resp.read() if resp.status == 200 else open("./tbd.png", "rb").read())
    await asyncio.gather(*[_dl(id) for id in ids])

    if lengthperline == -1: lengthperline = 15
    line = 0
    root = []
    for index in range(len(ids)):
        print(index, ids[index])
        imgpath = f"./cache/{ids[index]}.png"
        if not path.exists(imgpath) or not path.isfile(imgpath):
            open(imgpath, "wb").write(open("./tbd.png", "rb").read())

        img = Image.open(imgpath).resize((128, 128))
        if index == 0 and line == 0:
            root.append([img])
        if index-(lengthperline*line) >= lengthperline:
            line += 1
            root.append([img])
            #root = image.get_concat_h_blank(root, img)
        else:
            root[line].append(img)

        
    #return root.tobytes()
    get_concat_tile_resize(root).save(f:=io.BytesIO(), "jpeg")
    return f.getvalue()

async def main_async():
    session = aiohttp.ClientSession()
    print("Go to https://www.epicgames.com/id/api/redirect?clientId=3446cd72694c4a4485d81b77adbb2141&responseType=code and paste authorizationCode here;")
    authcode: str = input("Authorization Code: ")
    lpl: str = input("Length per Line: ")
    try:
        lpl = int(lpl)
    except:
        lpl = 25

    if not authcode:
        return print("authorization code pls")

    info = await authorize(authcode, session)
    if isinstance(info, str):
        return print(info)
    
    profile = await grabprofile(info, "athena", session)
    if isinstance(profile, str):
        return print(profile)
    items = []
    for item in profile['profileChanges'][0]['profile']['items'].values():
        id = item['templateId'].lower()
        if idpattern.match(id):
            items.append(id.split(':')[1])
    open(f"./{info['displayName']}.jpg", "wb").write(await createimg(items, lpl, f"https://github.com/pdf114514/FNSkinChecker/\nDisplayName: {info['displayName']}", session))
    await session.close()
    print("Done")

def main():
    asyncio.get_event_loop().run_until_complete(main_async())

if __name__ == "__main__":
    main()
