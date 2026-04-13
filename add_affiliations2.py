#!/usr/bin/env python3
"""
Second pass: Query DBLP for PIDs that were missed due to rate limiting.
Also uses known PIDs from community knowledge.
"""

import requests
import json
import time

# Known PIDs from community knowledge (to avoid re-querying)
KNOWN_PIDS = {
    "David H. Albonesi": "a/DavidHAlbonesi",
    "Jason Mars": "m/JasonMars",
    "Lingjia Tang": "t/LingjiaTang",
    "Jaehyuk Huh": "h/JaehyukHuh",
    "Jeremie S. Kim": "k/JeremieSKim",
    "Stefanos Kaxiras": "k/StefanosKaxiras",
    "Sreenivas Subramoney": "s/SreenivasSubramoney",
    "Alberto Ros": "r/AlbertoRos",
    "Ronald G. Dreslinski": "d/RonaldGDreslinski",
    "T. N. Vijaykumar": "v/TNVijaykumar",
    "Nandita Vijaykumar": "v/NanditaVijaykumar",
    "Konstantinos Kanellopoulos": "k/KonstantinosKanellopoulos",
    "Juan Gomez-Luna": "g/JuanGomezLuna",
    "Saugata Ghose": "g/SaugataGhose",
    "Eduard Ayguade": "a/EduardAyguade",
    "Simha Sethumadhavan": "s/SimhaSethumadhavan",
    "Shubhendu S. Mukherjee": "m/ShubhenduSMukherjee",
    "Steven K. Reinhardt": "r/StevenKReinhardt",
    "Phillip B. Gibbons": "g/PhillipBGibbons",
    "Sandhya Dwarkadas": "d/SandhyaDwarkadas",
    "Satish Narayanasamy": "n/SatishNarayanasamy",
    "Brandon Lucia": "l/BrandonLucia",
    "Rajiv Gupta": "g/RajivGupta",
    "Joseph Devietti": "d/JosephDevietti",
    "Kathryn S. McKinley": "m/KathrynSMcKinley",
    "Keshav Pingali": "p/KeshavPingali",
    "Mendel Rosenblum": "r/MendelRosenblum",
    "Michael M. Swift": "s/MichaelMSwift",
    "Steven Swanson": "s/StevenSwanson",
    "Yuanyuan Zhou": "z/YuanyuanZhou",
    "Henry Hoffmann": "h/HenryHoffmann",
    "Dan Tsafrir": "t/DanTsafrir",
    "Alvin R. Lebeck": "l/AlvinRLebeck",
    "Thomas M. Conte": "c/ThomasMConte",
    "Dirk Grunwald": "g/DirkGrunwald",
    "Bogong Su": "s/BogongSu",
    "Christos A. Papachristou": "p/ChristosAPapachristou",
    "Vicki H. Allan": "a/VickiHAllan",
    "Robert A. Mueller": "m/RobertAMueller",
    "Matthew Farrens": "f/MatthewFarrens",
    "Jorge Albericio": "a/JorgeAlbericio",
    "David W. Nellans": "n/DavidWNellans",
    "Ahmed Louri": "l/AhmedLouri",
    "Rui Hou": "h/RuiHou",
    "Lixin Zhang": "z/LixinZhang",
    "Xiaofei Liao": "l/XiaofeiLiao",
    "Lizhong Chen": "c/LizhongChen",
    "Mike O'Connor": "o/MikeOConnor",
    "Leibo Liu": "l/LeiboLiu",
    "Shaojun Wei": "w/ShaojunWei",
    "Tianshi Chen": "c/TianshiChen",
    "Yiannakis Sazeides": "s/YiannakisSazeides",
    "Timothy G. Rogers": "r/TimothyGRogers",
    "Nathan Beckmann": "b/NathanBeckmann",
    "Arkaprava Basu": "b/ArkapravaBasu",
    "Nael Abu-Ghazaleh": "a/NaelAbuGhazaleh",
    "Gennady Pekhimenko": "p/GennadyPekhimenko",
    "Gilles Pokam": "p/GillesPokam",
    "Hsien-Hsin S. Lee": "l/HsienHsinSLee",
    "Huiyang Zhou": "z/HuiyangZhou",
    "Amro Awad": "a/AmroAwad",
    "Adrián Cristal": "c/AdrianCristal",
    "Jayesh Gaur": "g/JayeshGaur",
    "Joel Emer": "e/JoelSEmer",  # Same as Joel S. Emer
    "John Kubiatowicz": "k/JohnKubiatowicz",
    "Mengjia Yan": "y/MengjiaYan",
    "Yang Hu": "h/YangHu2",
    "Mohammad Alian": "a/MohammadAlian",
    "Swamit Tannu": "t/SwamitTannu",
    "Yuhao Zhu": "z/YuhaoZhu",
    "Changhee Jung": "j/ChangheeJung",
    "Guangyu Sun": "s/GuangyuSun",
    "Hai Helen Li": "l/HaiHelenLi",
    "Yiran Chen": "c/YiranChen",
    "Engin Ipek": "i/EnginIpek",
    "Naveen Muralimanohar": "m/NaveenMuralimanohar",
    "Sudhanva Gurumurthi": "g/SudhanvaGurumurthi",
    "Jishen Zhao": "z/JishenZhao",
    # These need DBLP queries
    "Per Stenström": None,
    "John L. Hennessy": None,
    "Anant Agarwal": None,
    "Arvind": None,
    "Susan J. Eggers": None,
}

# Names that still need DBLP queries (failed in first run)
NEED_QUERY = [
    "Per Stenström",
    "John L. Hennessy",
    "Anant Agarwal",
    "Arvind",
    "Susan J. Eggers",
]

def search_dblp_pid(name):
    """Search DBLP for author PID."""
    url = "https://dblp.org/search/author/api"
    params = {"q": name, "format": "json", "h": 5}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("result", {}).get("hits", {}).get("hit", [])
        if not hits:
            return None
        for hit in hits:
            author_name = hit.get("info", {}).get("author", "")
            pid = hit.get("info", {}).get("url", "")
            if "/pid/" in pid:
                pid = pid.split("/pid/")[1]
            return {"pid": pid, "dblp_name": author_name}
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

# Query missing ones
for name in NEED_QUERY:
    print(f"Querying: {name}...")
    result = search_dblp_pid(name)
    if result:
        KNOWN_PIDS[name] = result["pid"]
        print(f"  -> {result['dblp_name']}: {result['pid']}")
    else:
        KNOWN_PIDS[name] = ""
        print(f"  -> NOT FOUND")
    time.sleep(5)

# Now load the first pass results and merge
with open("C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/new_affiliations.json", "r", encoding="utf-8") as f:
    results = json.load(f)

# Update PIDs
for entry in results:
    name = entry["name"]
    if not entry["pid"] and name in KNOWN_PIDS:
        entry["pid"] = KNOWN_PIDS[name] or ""

# Save updated results
with open("C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/new_affiliations.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\n\n=== FINAL JS CODE ===")
for entry in results:
    pid = entry["pid"] or ""
    name = entry["name"]
    inst = entry["inst"]
    print(f'  "{name}": {{inst:"{inst}",pid:"{pid}"}},')

print(f"\nTotal: {len(results)}")
