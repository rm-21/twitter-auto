import argparse
import asyncio
import datetime as dt
import sys

import httpx

from .cookies import get_session_info


async def _subscribe(
    bearer_token: str,
    auth_token: str,
    csrf_token: str,
    user_id_to_subscribe_to: int,
) -> bool:
    url = "https://x.com/i/api/1.1/friendships/create.json"
    async with httpx.AsyncClient(timeout=120) as client:
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Bearer {bearer_token}",
            "content-type": "application/x-www-form-urlencoded",
            "cookie": f"auth_token={auth_token}; ct0={csrf_token}",
            "origin": "https://x.com",
            "priority": "u=1, i",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "x-csrf-token": csrf_token,
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
        }

        res = await client.post(
            url=url,
            headers=headers,
            data={
                "include_profile_interstitial_type": 1,
                "include_blocking": 1,
                "include_blocked_by": 1,
                "include_followed_by": 1,
                "include_want_retweets": 1,
                "include_mute_edge": 1,
                "include_can_dm": 1,
                "include_can_media_tag": 1,
                "include_ext_is_blue_verified": 1,
                "include_ext_verified_type": 1,
                "include_ext_profile_image_shape": 1,
                "skip_status": 1,
                "user_id": user_id_to_subscribe_to,
            },
        )

        if res.status_code == 200:
            print(
                f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Followed: {res.json()["screen_name"]}"
            )
            return True
        else:
            print(
                f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed for ID: {user_id_to_subscribe_to}"
            )
            return False


async def _subscribe_multiple(
    bearer_token: str,
    auth_token: str,
    csrf_token: str,
    user_ids_to_subscribe_to: list[int],
) -> None:
    for _id in user_ids_to_subscribe_to:
        await _subscribe(
            bearer_token=bearer_token,
            auth_token=auth_token,
            csrf_token=csrf_token,
            user_id_to_subscribe_to=_id,
        )
        await asyncio.sleep(2)

    return None


def _read_ids(loc: str) -> list[int]:
    ids: list[int] = []
    with open(loc, "r") as file:
        for line in file:
            ids.append(int(line.strip().split("=")[-1]))
    return ids


async def subscribe(
    email: str,
    username: str,
    password: str,
    file_loc: str,
) -> None:
    # Read IDs
    try:
        ids = _read_ids(loc=file_loc)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"File '{file_loc}' does not exist. Please check the path provided."
        )

    # Get Session info
    try:
        info = get_session_info(
            email=email,
            username=username,
            password=password,
        )

        if not info:
            raise Exception("Could not retrieve session info")

        if not info["bearer_token"]:
            raise ValueError("Could not retreive `bearer_token`")
        if not info["auth_token"]:
            raise ValueError("Could not retreive `auth_token`")
        if not info["csrf_token"]:
            raise ValueError("Could not retreive `csrf_token`")

    except Exception as exc:
        raise Exception(f"Could not retrieve session info: {exc}")

    # Subscribe
    await _subscribe_multiple(
        bearer_token=info["bearer_token"],
        auth_token=info["auth_token"],
        csrf_token=info["csrf_token"],
        user_ids_to_subscribe_to=ids,
    )

    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Subscribe to multiple users using provided credentials and ID file."
    )

    parser.add_argument(
        "-e", "--email", required=True, help="Email address for authentication"
    )

    parser.add_argument(
        "-u", "--username", required=True, help="Username for authentication"
    )

    parser.add_argument(
        "-p", "--password", required=True, help="Password for authentication"
    )

    parser.add_argument(
        "-f", "--file", required=True, help="Path to the file containing user IDs"
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            subscribe(
                email=args.email,
                username=args.username,
                password=args.password,
                file_loc=args.file,
            )
        )
        print("Successfully subscribed to all users!")
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
