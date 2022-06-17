"""
   Copyright 2020-2022 Yufan You <https://github.com/ouuan>
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import requests
import json
import sys
import re

if __name__ == "__main__":
    assert(len(sys.argv) == 4)
    handle = sys.argv[1]
    token = sys.argv[2]
    readmePath = sys.argv[3]

    headers = {
        "Authorization": f"token {token}"
    }

    followers = []
    cursor = None

    while True:
        query = f'''
query {{
    user(login: "{handle}") {{
        followers(first: 100{f', after: "{cursor}"' if cursor else ''}) {{
            pageInfo{{
                endCursor
                hasNextPage
            }}
            nodes {{
                login
                name
                databaseId
                following {{
                    totalCount
                }}
                repositories(first: 3, isFork: false, orderBy: {{
                    field: STARGAZERS,
                    direction: DESC
                }}) {{
                    totalCount
                    nodes {{
                        stargazerCount
                    }}
                }}
                followers {{
                    totalCount
                }}
            }}
        }}
    }}
}}
'''
        response = requests.post(f"https://api.github.com/graphql", json.dumps({ "query": query }), headers = headers)
        res = response.json()["data"]["user"]["followers"]
        for follower in res["nodes"]:
            following = follower["following"]["totalCount"]
            repoCount = follower["repositories"]["totalCount"]
            login = follower["login"]
            name = follower["name"]
            id = follower["databaseId"]
            followerNumber = follower["followers"]["totalCount"]
            thirdStars = follower["repositories"]["nodes"][2]["stargazerCount"] if repoCount >= 3 else 0
            if following > thirdStars * 50 + repoCount * 5 + followerNumber:
                print(f"Skipped: https://github.com/{login} with {followerNumber} followers and {following} following")
                continue
            followers.append((followerNumber, login, id, name if name else login))
            print(followers[-1])
        if not res["pageInfo"]["hasNextPage"]:
            break
        cursor = res["pageInfo"]["endCursor"]

    followers.sort(reverse = True)

    html = "<table>\n"

    for i in range(min(len(followers), 21)):
        login = followers[i][1]
        id = followers[i][2]
        name = followers[i][3]
        if i % 7 == 0:
            if i != 0:
                html += "  </tr>\n"
            html += "  <tr>\n"
        html += f'''    <td align="center">
      <a href="https://github.com/{login}">
        <img src="https://avatars2.githubusercontent.com/u/{id}" width="100px;" alt="{login}"/>
      </a>
      <br />
      <a href="https://github.com/{login}">{name}</a>
    </td>
'''

    html += "  </tr>\n</table>"

    with open(readmePath, "r") as readme:
        content = readme.read()

    newContent = re.sub(r"(?<=<!\-\-START_SECTION:top\-followers\-\->)[\s\S]*(?=<!\-\-END_SECTION:top\-followers\-\->)", f"\n{html}\n", content)

    with open(readmePath, "w") as readme:
        readme.write(newContent)