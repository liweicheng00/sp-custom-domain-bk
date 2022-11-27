import aiohttp
import datetime
from app.config import settings


def get_query_string(timestamp, skip):
    return {
        "query":
            f""" query {{
              tokenTransfers(
                where: {{timestamp_gte: "{timestamp}"}}
                orderBy: timestamp
                orderDirection: asc
                first: 500
                skip: {skip}
              ) {{
                timestamp
                id
                from
                to
                nft {{
                  id
                }}
              }}
            }}"""
    }


async def subgraph_mission():
    """Scheduled job for subgraph query."""
    timestamp = int(datetime.datetime.now().timestamp()) - 60
    for i in range(0, 3000, 500):
        data = get_query_string(timestamp, i)
        async with aiohttp.ClientSession() as session:
            async with session.post(settings.graph_url, json=data) as res:
                transfer_data = await res.json()
                transfer_data = transfer_data['data']['tokenTransfers']
                print(transfer_data)
