#!/usr/bin/env python3
"""
Query DBLP for author PIDs and generate JS affiliations entries.
Skips researchers already in the affiliations section.
"""

import requests
import json
import time

# Already in affiliations (current data.js entries) - skip these
ALREADY_IN = {
    "Onur Mutlu", "Josep Torrellas", "Yale N. Patt", "Nam Sung Kim",
    "Yuan Xie", "Scott A. Mahlke", "Moinuddin K. Qureshi", "Babak Falsafi",
    "Frederic T. Chong", "Wen-Mei W. Hwu", "Margaret Martonosi",
    "Trevor N. Mudge", "David Brooks", "Dean M. Tullsen", "Mark D. Hill",
    "David A. Wood", "Daniel Sanchez", "Xuehai Qian", "Lieven Eeckhout",
    "Thomas F. Wenisch", "Mahmut Taylan Kandemir", "Stephen W. Keckler",
    "Gurindar S. Sohi", "Christos Kozyrakis", "John Kim", "William J. Dally",
    "Chita R. Das", "Parthasarathy Ranganathan", "Gabriel H. Loh",
    "Mikko H. Lipasti", "Doug Burger", "Jung Ho Ahn", "Aamer Jaleel",
    "Rajeev Balasubramonian", "Murali Annavaram", "Minsoo Rhu",
    "Christopher W. Fletcher", "Vijaykrishnan Narayanan", "André Seznec",
    "Reetuparna Das", "Gu-Yeon Wei", "Tushar Krishna", "Rakesh Kumar",
    "Natalie D. Enright Jerger", "Brad Calder", "David I. August",
    "Pradip Bose", "Prashant J. Nair", "Joel S. Emer", "Timothy Sherwood",
    "Antonio González", "Mateo Valero", "Yan Solihin", "Youtao Zhang",
    "Jun Yang", "Anand Sivasubramaniam", "Alper Buyuktosunoglu",
    "Mattan Erez", "Hyesoon Kim", "A. Giray Yağlıkçı",
    "Mohammad Sadrosadati", "Abhishek Bhattacharjee", "Christina Delimitrou",
    "Luis Ceze", "Shan Lu", "Krste Asanovic", "Kunle Olukotun",
    "Sarita V. Adve", "Norman P. Jouppi", "David A. Patterson",
    "Mark Horowitz", "Tor M. Aamodt", "Hai Jin", "Mingyu Gao", "Chao Li",
    "Minyi Guo", "Jingwen Leng", "Xing Hu", "Qi Guo", "Jian Huang",
    "James E. Smith", "Jae W. Lee", "Yufei Ding", "Jangwoo Kim",
    "Henry M. Levy", "Won Woo Ro", "Myoungsoo Jung", "Shouyi Yin",
    "Carole-Jean Wu", "Vijay Janapa Reddi", "Ricardo Bianchini",
    "Boris Grot", "Hadi Esmaeilzadeh", "Daniel J. Sorin", "Kevin Skadron",
    "Todd M. Austin", "Karin Strauss",
    # Variant names that norm() handles
    "Todd Austin", "Scott Mahlke", "Trevor Mudge", "Daniel Sánchez",
    "Wen-mei W. Hwu",
}

# Researchers to add: name -> institution
# Skipping: Todd Austin, Scott Mahlke, Trevor Mudge (covered by norm()),
#           Daniel Sanchez/Sánchez (already in), Wen-mei Hwu (already in),
#           Joel Emer (already as Joel S. Emer), Boris Grot (already in)
RESEARCHERS = [
    ("Per Stenström", "Chalmers"),
    ("John L. Hennessy", "Stanford"),
    ("Anant Agarwal", "MIT"),
    ("Arvind", "MIT"),
    ("Susan J. Eggers", "UW (emeritus)"),
    ("Todd C. Mowry", "CMU"),
    ("Kourosh Gharachorloo", "Google (retired)"),
    ("James R. Goodman", "UW-Madison (emeritus)"),
    ("Jean-Loup Baer", "UW (emeritus)"),
    ("G. Jack Lipovski", "UT Austin (emeritus)"),
    ("Janak H. Patel", "UIUC (emeritus)"),
    ("Edward S. Davidson", "U Michigan (emeritus)"),
    ("Howard Jay Siegel", "Colorado State"),
    ("Michel Dubois", "USC (emeritus)"),
    ("Andrew R. Pleszkun", "U Colorado"),
    ("Pen-Chung Yew", "U Minnesota"),
    ("John Paul Shen", "CMU"),
    ("David E. Culler", "UC Berkeley / Google"),
    ("Anoop Gupta", "Google"),
    ("Bob Ramakrishna Rau", "HP Labs (deceased)"),
    ("Mark Oskin", "UW"),
    ("David Wentzlaff", "Princeton"),
    ("Karthikeyan Sankaralingam", "UW-Madison"),
    ("Sanjay J. Patel", "UIUC"),
    ("Chris Wilkerson", "Intel"),
    ("Christopher J. Hughes", "Intel"),
    ("Eric Rotenberg", "NC State"),
    ("Gary S. Tyson", "FSU"),
    ("Li-Shiuan Peh", "NUS"),
    ("Ang Li", "PNNL"),
    ("Benjamin C. Lee", "U Penn"),
    ("Donghyuk Lee", "NVIDIA"),
    ("Michael C. Huang", "U Rochester"),
    ("David H. Albonesi", "Cornell"),
    ("Jason Mars", "U Michigan"),
    ("Lingjia Tang", "U Michigan"),
    ("Jaehyuk Huh", "KAIST"),
    ("Jeremie S. Kim", "ETH Zurich"),
    ("Stefanos Kaxiras", "Uppsala"),
    ("Sreenivas Subramoney", "Intel"),
    ("Alberto Ros", "U Murcia"),
    ("Ronald G. Dreslinski", "U Michigan"),
    ("T. N. Vijaykumar", "Purdue"),
    ("Nandita Vijaykumar", "U Toronto"),
    ("Konstantinos Kanellopoulos", "ETH Zurich"),
    ("Juan Gomez-Luna", "ETH Zurich"),
    ("Saugata Ghose", "UIUC"),
    ("Eduard Ayguade", "UPC Barcelona"),
    ("Simha Sethumadhavan", "Columbia"),
    ("Shubhendu S. Mukherjee", "Nvidia"),
    ("Steven K. Reinhardt", "AMD"),
    ("Phillip B. Gibbons", "CMU"),
    ("Sandhya Dwarkadas", "U Rochester / Yale"),
    ("Satish Narayanasamy", "U Michigan"),
    ("Brandon Lucia", "CMU"),
    ("Rajiv Gupta", "UC Riverside"),
    ("Joseph Devietti", "U Penn"),
    ("Kathryn S. McKinley", "Google"),
    ("Keshav Pingali", "UT Austin"),
    ("Mendel Rosenblum", "Stanford"),
    ("Michael M. Swift", "UW-Madison"),
    ("Steven Swanson", "UCSD"),
    ("Yuanyuan Zhou", "UCSD"),
    ("Henry Hoffmann", "U Chicago"),
    ("Dan Tsafrir", "Technion"),
    ("Alvin R. Lebeck", "Duke"),
    ("Thomas M. Conte", "Georgia Tech"),
    ("Dirk Grunwald", "U Colorado"),
    ("Bogong Su", "retired"),
    ("Christos A. Papachristou", "Case Western"),
    ("Vicki H. Allan", "Utah State"),
    ("Robert A. Mueller", "retired"),
    ("Matthew Farrens", "UC Davis"),
    ("Jorge Albericio", "NVIDIA"),
    ("David W. Nellans", "NVIDIA"),
    ("Ahmed Louri", "GWU"),
    ("Rui Hou", "ICT-CAS"),
    ("Lixin Zhang", "ICT-CAS"),
    ("Xiaofei Liao", "HUST"),
    ("Lizhong Chen", "Oregon State"),
    ("Mike O'Connor", "NVIDIA / UT Austin"),
    ("Leibo Liu", "Tsinghua"),
    ("Shaojun Wei", "Tsinghua"),
    ("Tianshi Chen", "CASIA"),
    ("Yiannakis Sazeides", "U Cyprus"),
    ("Timothy G. Rogers", "Purdue"),
    ("Nathan Beckmann", "CMU"),
    ("Arkaprava Basu", "IISc Bangalore"),
    ("Nael Abu-Ghazaleh", "UC Riverside"),
    ("Gennady Pekhimenko", "U Toronto"),
    ("Gilles Pokam", "Intel"),
    ("Hsien-Hsin S. Lee", "TSMC / Georgia Tech"),
    ("Huiyang Zhou", "NC State"),
    ("Amro Awad", "NC State"),
    ("Adrián Cristal", "BSC Barcelona"),
    ("Jayesh Gaur", "Intel"),
    ("Joel Emer", "MIT / NVIDIA"),   # Note: Joel S. Emer already in, but "Joel Emer" variant
    ("John Kubiatowicz", "UC Berkeley"),
    ("Mengjia Yan", "MIT"),
    ("Yang Hu", "U Rochester"),
    ("Mohammad Alian", "U Kansas"),
    ("Swamit Tannu", "UW-Madison"),
    ("Yuhao Zhu", "U Rochester"),
    ("Changhee Jung", "Purdue"),
    ("Guangyu Sun", "Peking U"),
    ("Hai Helen Li", "Duke"),
    ("Yiran Chen", "Duke"),
    ("Engin Ipek", "U Rochester"),
    ("Naveen Muralimanohar", "HP Labs / Micron"),
    ("Sudhanva Gurumurthi", "AMD"),
    ("Jishen Zhao", "UCSD"),
    ("David Blaauw", "U Michigan"),
    ("Xiaoyao Liang", "SJTU"),
    ("Shuangchen Li", "Samsung"),
    ("Zeshan Chishti", "Intel"),
    ("Youfeng Wu", "Intel"),
    ("Minesh Patel", "ETH Zurich"),
    ("Ataberk Olgun", "ETH Zurich"),
    ("Christopher Batten", "Cornell"),
    ("Daehoon Kim", "Yonsei U"),
    ("Daniel A. Jiménez", "Texas A&M"),
    ("G. Edward Suh", "Cornell / Meta"),
    ("José F. Martínez", "Cornell"),
    ("José-María Arnau", "UPC Barcelona"),
    ("Milos Prvulovic", "Georgia Tech"),
    ("Ravishankar R. Iyer", "Intel"),
    ("Xiaowei Jiang", "NUDT"),
    ("John B. Carter", "IBM"),
    ("José Duato", "UPV Valencia"),
    ("Luiz André Barroso", "Google (retired)"),
]

def search_dblp_pid(name):
    """Search DBLP for author PID. Returns best match or None."""
    url = "https://dblp.org/search/author/api"
    params = {"q": name, "format": "json", "h": 5}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        hits = data.get("result", {}).get("hits", {}).get("hit", [])
        if not hits:
            return None
        # Try exact match first
        for hit in hits:
            author_name = hit.get("info", {}).get("author", "")
            pid = hit.get("info", {}).get("url", "")
            # Extract PID from URL like https://dblp.org/pid/m/OnurMutlu
            if "/pid/" in pid:
                pid = pid.split("/pid/")[1]
            elif pid.startswith("https://dblp.org/pid/"):
                pid = pid[len("https://dblp.org/pid/"):]
            # Check if name matches (case insensitive, ignore middle initials)
            name_parts = set(name.lower().replace(".", "").split())
            author_parts = set(author_name.lower().replace(".", "").split())
            # At least first and last name should match
            if name_parts & author_parts:
                return {"pid": pid, "dblp_name": author_name}
        # Return first result if no exact match
        hit = hits[0]
        pid = hit.get("info", {}).get("url", "")
        if "/pid/" in pid:
            pid = pid.split("/pid/")[1]
        author_name = hit.get("info", {}).get("author", "")
        return {"pid": pid, "dblp_name": author_name}
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def main():
    results = []

    for name, inst in RESEARCHERS:
        # Skip if already in affiliations
        if name in ALREADY_IN:
            print(f"  SKIP (already in): {name}")
            continue

        print(f"Querying: {name}...")
        result = search_dblp_pid(name)

        entry = {
            "name": name,
            "inst": inst,
            "pid": None,
            "dblp_name": None,
        }

        if result:
            entry["pid"] = result["pid"]
            entry["dblp_name"] = result["dblp_name"]
            print(f"  Found: {result['dblp_name']} -> {result['pid']}")
        else:
            print(f"  NOT FOUND")

        results.append(entry)
        time.sleep(3)  # Rate limiting

    # Save to JSON
    with open("C:/Users/Z GAMES/Yapay Zeka/CompArch-HallOfFame/new_affiliations.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n\n=== JS CODE TO ADD ===")
    print("// New affiliations to add:")
    for entry in results:
        pid = entry["pid"] or ""
        js_line = f'  "{entry["name"]}": {{inst:"{entry["inst"]}",pid:"{pid}"}},'
        print(js_line)

    print(f"\nTotal new entries: {len(results)}")
    print("Saved to new_affiliations.json")

if __name__ == "__main__":
    main()
