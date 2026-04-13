"""
Count HPCA 2026 papers for existing HoF members from the DBLP listing.
"""
import re, json

# HPCA 2026 author list (pasted from DBLP)
hpca2026_raw = """
Junghoon Kim, Jongheon Jeong, Seokwon Moon, Seong Hoon Seo, Yeonhong Park, Jinkyu Jeong, Nam Sung Kim, Jae W. Lee
Shuang Liang, Yuncheng Lu, Ce Guo, Paul H. J. Kelly, Wayne Luk, Hongxiang Fan
Junguk Hong, Changmin Shin, Sukjin Kim, Si Ung Noh, Taehee Kwon, Seongyeon Park, Hanjun Kim, Youngsok Kim, Jinho Lee
Joongun Park, Yongqin Wang, Huan Xu, Hanjiang Wu, Mengyuan Li, Tushar Krishna
Xinhua Chen, Jiangbin Dong, Hongren Zheng, Tian Tang, Mingyu Gao
Baiqing Zhong, Zhirong Ye, Xiaojie Li, Peilin Wang, Haiqiu Huang, Zhaolin Li, Zhiyi Yu, Mingyu Wang
Fangzhou Ye, Lingxiang Yin, Hao Zheng
Alexander Knapen, Guanchen Tao, Jacob Mack, Tomas Bruno, Mehdi Saligane, Dennis Sylvester, Qirui Zhang, Gokul Subramanian Ravi
Minh S. Q. Truong, Yiqiu Sun, Dawei Xiong, Amol Shah, Alexander Glass, Abraham Farrell, James A. Bain, L. Richard Carley, Saugata Ghose
Huizheng Wang, Hongbin Wang, Zichuan Wang, Zhiheng Yue, Yang Wang, Chao Li, Yang Hu, Shouyi Yin
Lin Wang, Yuchong Hu, Ziling Duan, Mingqi Li, Chenxuan Yao, Feifan Liu, Xiaolu Li, Leihua Qin, Dan Feng
Peter W. Deutsch, Harish Dattatraya Dixit, Gautham Vunnam, Carl Moran, Eleanor Ozer, Sriram Sankar
Junseo Lee, Sangyun Jeon, Jungi Lee, Junyong Park, Jaewoong Sim
Zheng Xu, Dehao Kong, Jiaxin Liu, Dingcheng Jiang, Xu Dai, Jinyi Deng, Yang Hu, Shouyi Yin
Chuhao Xu, Zijun Li, Quan Chen, Han Zhao, Xueyan Tang, Minyi Guo
Haoqi He, Zhiwei Wang, Lutan Zhao, Dian Jiao, Dan Meng, Rui Hou
David Schall, Maria Durackova, Boris Grot
Qingyun Niu, Lutan Zhao, Ming Cai, Kai Li, Dan Meng, Rui Hou
Suhas K. Vittal, Moinuddin Qureshi
Zifei Zhang, Yinan Xu, Sa Wang, Dan Tang, Yungang Bao
Benjamin F. Morris III, Tergel Molom-Ochir, Changchun Zhou, Yiran Chen, Alex K. Jones, Hai Li
Haomin Li, Yun Liang, Fangxin Liu, Bowen Zhu, Zongwu Wang, Yu Feng, Liqiang Lu, Li Jiang, Haibing Guan
Hyungyo Kim, Qirong Xia, Jinghan Huang, Nachuan Wang, Younjoo Lee, Jung Ho Ahn, Wajdi K. Feghali, Ren Wang, Nam Sung Kim
Moinuddin K. Qureshi
Yang Zhong, Haoran Wu, Xueqi Li, Sa Wang, David Boland, Yungang Bao, Kan Shi
Xinkai Wang, Chao Li, Yiming Zhuansun, Jinyang Guo, Xiaofeng Hou, Jing Wang, Luping Wang, Weigao Chen, Cheng Huang, Guodong Yang, Liping Zhang, Minyi Guo
Xiaotong Huang, He Zhu, Tianrui Ma, Yuxiang Xiong, Fangxin Liu, Zhezhi He, Yiming Gan, Zihan Liu, Jingwen Leng, Yu Feng, Minyi Guo
Guangyang Deng, Zixiang Yu, Zhirong Shen, Qiangsheng Su, Zhinan Cheng, Jiwu Shu
Yanjing Wang, Lizhou Wu, Sunfeng Gao, Yibo Tang, Junhui Luo, Zicong Wang, Yang Ou, Dezun Dong, Nong Xiao, Mingche Lai
Wenhao Huang, Zhaolin Duan, Laiping Zhao, Yuhao Zhang, Yanjie Wang, Yiming Li, Yihan Wang, Yichi Chen, Zhihang Tang, Kang Chen, Deze Zeng, Wenxin Li, Keqiu Li
Hanyu Zhang, Fangxu Guo, Liqiang Lu, Long Wang, Yunfei Du, Zhe Wang, Jinghan Zhang, Jie Zhang, Chenli Xue, Chengpeng Wu, Ziyi Zhang, Yun Liang, Size Zheng, Jianwei Yin
Anbang Wu, Liqiang Lu, Jianwei Yin, Jingwen Leng, Minyi Guo
Taishu Sheng, Guangyu Sun, Dezun Dong
Zhantong Qiu, Mahyar Samani, Jason Lowe-Power
Carlos Escuin, Paolo Salvatore Galfano, Davide Basilio Bartolini, Leeor Peled, Mehdi Alipour
Ming Wang, Ang Li, Frank Mueller
Xu Jiang, Xueliang Wei, Yifei Qu, Dan Feng, Yulai Xie, Wei Tong
Sehyeon Kim, Minkwan Kim, Chanho Park, Hanmok Park, Seonghoon Kim, Taigon Song, William J. Song
Anatole Lefort, David Schall, Nicolo Carpentieri, Julian Pritzi, Soham Chakraborty, Nicolai Oswald, Pramod Bhatotia
Chang Liu, Hongpei Zheng, Xin Zhang, Dapeng Ju, Dongsheng Wang, Yinqian Zhang, Trevor E. Carlson
Fuyu Wang, Minghua Shen, Yufei Ding, Nong Xiao, Yutong Lu
Nicholas Mosier, Hamed Nemati, John C. Mitchell, Caroline Trippel
Han Zhao, Weihao Cui, Zeshen Zhang, Wenhao Zhang, Jiangtong Li, Quan Chen, Pu Pang, Zijun Li, Zhenhua Han, Yuqing Yang, Minyi Guo
Xinru Tang, Jingxiang Hou, Dingcheng Jiang, Taiquan Wei, Jiaxin Liu, Jinyi Deng, Huizheng Wang, Qize Yang, Haoran Shang, Chao Li, Yang Hu, Shouyi Yin
Zehao Chen, Zhaoyan Shen, Qian Wei, Hang Lu, Lei Ju
Yilan Zhu, Geng Yang, Xingyu Tian, Dilshan Kumarathunga, Liang Kong, Xianglong Deng, Shengyu Fan, Guang Fan, Guiming Shi, Lei Chen, Bo Zhang, Yisong Chang, Shoumeng Yan, Zhenman Fang, Mingzhe Zhang
Alhad Daftardar, Jianqiao Mo, Joey Ah-kiow, Benedikt Bunz, Siddharth Garg, Brandon Reagen
Deanna Postles Dunn Berger, Alper Buyuktosunoglu, Craig R. Walters, Robert J. Sonnelitter, Hailey Nicholson, Ashraf ElSharif, Yamil Rivera, Avery Francois, Cedric Lichtenau, Jason Kohl
Xiaochuan Tang, Hao Qi, Jianbo Dong, Yinghao Yu, Zhennan Xue, Zhengyu Zhang, Daocheng Ying, Zheng Cao, Xiaoyi Lu
Sangjin Kim, Yuseon Chou, Byeongcheol Kim, Jungjun Oh, Hoi-Jun Yoo
Yaoyun Zhou, Qian Wang
Jiuchen Shi, Hang Zhang, Yixiao Wang, Quan Chen, Yizhou Shan, Kaihua Fu, Wei Wang, Minyi Guo
Jinwoo Park, John Kim
Donghyuk Kim, Sejeong Yang, Wonjin Shin, Joo-Young Kim
Fan Li, Qiufeng Li, Yanan Guo, Weidong Cao, Xin Xin
Junkyum Kim, Divya Mahajan
Hongshi Tan, Yao Chen, Xinyu Chen, Qizhen Zhang, Cheng Chen, Weng-Fai Wong, Bingsheng He
Chen Zhang, Qijun Zhang, Zhuoshan Zhou, Yijia Diao, Haibo Wang, Zhe Zhou, Zhipeng Tu, Zhiyao Li, Guangyu Sun, Zhuoran Song, Zhigang Ji, Jingwen Leng, Minyi Guo
Qixuan Yu, David Wentzlaff
Yuzhe Fu, Changchun Zhou, Hancheng Ye, Bowen Duan, Qiyu Huang, Chiyue Wei, Cong Guo, Hai Helen Li, Yiran Chen
Yi Li, Tsun-Yu Yang, Zhaoyan Shen, Ming-Chang Yang, Bingzhe Li
Nicolas Meseguer, Daoxuan Xu, Yifan Sun, Michael Pellauer, Jose L. Abellan, Manuel E. Acacio
Jianming Tong, Tianhao Huang, Jingtian Dang, Leo de Castro, Anirudh Itagi, Anupam Golder, Asra Ali, Jeremy Kun, Jevin Jiang, Arvind, G. Edward Suh, Tushar Krishna
Huizheng Wang, Taiquan Wei, Zichuan Wang, Dingcheng Jiang, Qize Yang, Jiaxin Liu, Jingxiang Hou, Chao Li, Jinyi Deng, Yang Hu, Shouyi Yin
Chengran Li, Huizheng Wang, Jiaxin Liu, Jingyao Liu, Zhiheng Yue, Xia Li, Shenfei Jiang, Jinyi Deng, Yang Hu, Shouyi Yin
Hyucksung Kwon, Kyungmo Koo, Janghyeon Kim, Woongkyu Lee, Minjae Lee, Gyeonggeun Jung, Hyungdeok Lee, Yousub Jung, Jaehan Park, Yosub Song, Byeongsu Yang, Haerang Choi, Guhyun Kim, Jongsoon Won, Woojae Shin, Changhyun Kim, Gyeongcheol Shin, Yongkee Kwon, Ilkon Kim, Euicheol Lim, John Kim, Jungwook Choi
Runze Wang, Qinggang Wang, Haifeng Liu, Long Zheng, Xiaofei Liao, Hai Jin, Jingling Xue
Zhen He, Yiqi Wang, Zhiheng Yue, Zihan Wu, Huiming Han, Shaojun Wei, Yang Hu, Fengbin Tu, Shouyi Yin
Sangwoo Hwang, Donghun Lee, Jahyun Koo, Jaeha Kung
Jinyu Hu, Huizhang Luo, Hong Jiang, Marc Casas, Kenli Li, Chubo Liu
Zhiqiang Chen, Wenwen Fu, Yongwen Wang, Hongwei Zhou
Yuanyuan Wang, Nana Tang, Yuyang Wang, Shu Pan, Dingding Yu, Zeyue Wang, Mou Sun, Kejie Fu, Fangyu Wang, Yunchuan Chen, Ning Sun, Fei Yang
Huizheng Wang, Zichuan Wang, Hongbin Wang, Jingxiang Hou, Taiquan Wei, Chao Li, Yang Hu, Shouyi Yin
Hritvik Taneja, Ali Hajiabadi, Michele Marazzi, Kaveh Razavi, Moinuddin Qureshi
Sanghyun Kim, Jinhyeok Oh, Taehun Kim, Gyutae Kim, Youngsok Kim, Jaehyun Hwang, Joonsung Kim
Hyunkyun Shin, Seongtae Bang, Hyungwon Park, Daehoon Kim
Nika Mansouri-Ghiasi, Talu Guloglu, Harun Mustafa, Can Firtina, Konstantina Koliogeorgi, Konstantinos Kanellopoulos, Haiyu Mao, Rakesh Nadig, Mohammad Sadrosadati, Jisung Park, Onur Mutlu
Chihun Song, Austin Antony Cruz, Michael Jaemin Kim, Minbok Wi, Gaohan Ye, Kyungsan Kim, Sangyeol Lee, Jung Ho Ahn, Nam Sung Kim
Rahul Bera, Zhenrong Lang, Caroline Hengartner, Konstantinos Kanellopoulos, Rakesh Kumar, Mohammad Sadrosadati, Onur Mutlu
Ziyu Huang, Yangjie Zhou, Zihan Liu, Xinhao Luo, Yijia Diao, Minyi Guo, Jidong Zhai, Yu Feng, Chen Zhang, Anbang Wu, Jingwen Leng
Zishen Wan, Che-Kai Liu, Jiaqi Qian, Hanchen Yang, Arijit Raychowdhury, Tushar Krishna
Seungkwan Kang, Seungjun Lee, Donghyun Gouk, Miryeong Kwon, Hyunkyu Choi, Junhyeok Jang, Sangwon Lee, Huiwon Choi, Jie Zhang, Wonil Choi, Mahmut Taylan Kandemir, Myoungsoo Jung
Dongjae Lee, Bongjoon Hyun, Youngjin Kwon, Minsoo Rhu
Joao Paulo C. de Lima, Benjamin F. Morris III, Asif Ali Khan, Jeronimo Castrillon, Alex K. Jones
Pranati Majhi, Sabuj Laskar, Abdullah Muzahid, Eun Jung Kim
Ben Chen, Kunlin Li, Shuwen Deng, Dongsheng Wang, Yun Chen
Changheon Lee, Hyungseok Kim, Seungwoo Choi, Youngmin Kim, Won Woo Ro
Shunchen Shi, Qijia Yang, Fan Yang, Yu Huang, Youwei Zhuo, Zhichun Li, Ninghui Sun, Xueqi Li
Daoxuan Xu, Ying Li, Yuwei Sun, Jie Ren, Yifan Sun
Kosuke Matsushima, Yasuyuki Okoshi, Masato Motomura, Daichi Fujiki
Yiquan Lin, Wenhai Lin, Yiquan Chen, Jiexiong Xu, Shishun Cai, Jiarong Ye, Zonghui Wang, Wenzhi Chen
Enhyeok Jang, Hyungseok Kim, Yongju Lee, Jaewon Kwon, Yipeng Huang, Won Woo Ro
Chiyue Wei, Cong Guo, Junyao Zhang, Haoxuan Shan, Yifan Xu, Ziyue Zhang, Yudong Liu, Qinsi Wang, Changchun Zhou, Hai Helen Li, Yiran Chen
Yecheng Xue, Rui Yang, Zhiding Liang, Tongyang Li
Rui Wen, Zhifei Yue, Tianbo Liu, Xinkai Song, Jin Li, Di Huang, Jiaming Guo, Xing Hu, Zidong Du, Qi Guo, Tianshi Chen
Xujiang Xiang, Fengbin Tu
Theodoros Trochatos, Christopher Kang, Andrew Wang, Frederic T. Chong, Jakub Szefer
Hamed Seyedroudbari, Alexandros Daglis
Dayou Du, Shijie Cao, Jianyi Cheng, Luo Mai, Ting Cao, Mao Yang
Quang Duong, Calvin Lin
Zhezheng Ren, Chenao Yuan, Yuke Zhang, Shiyu Su
Jiin Kim, Byeongjun Shin, Jinha Chung, Minsoo Rhu
Matthew Joseph Adiletta, Gu-Yeon Wei, David Brooks
Anjunyi Fan, Xuejie Liu, Anji Liu, Qiuping Wu, Jiaqi Yang, Yuchao Qin, Guy Van den Broeck, Yitao Liang, Bonan Yan
Xingyu Liu, Jiawei Liang, Yipu Zhang, Linfeng Du, Chaofang Ma, Hui Yu, Jiang Xu, Wei Zhang
Hongrui Guo, Tianrui Ma, Zidong Du, Mo Zou, Yifan Hao, Yongwei Zhao, Rui Zhang, Wei Li, Xing Hu, Zhiwei Xu, Qi Guo, Tianshi Chen
Chenglin Wang, Shouxin Wang, Zhirong Shen, Lu Tang, Shuyue Zhou, Ronglong Wu, Min Zhou, Jialiang Yu, Yiming Zhang
Julien Eudine, Chu Li, Zhuo Cheng, Renzo Andri, Can Firtina, Mohammad Sadrosadati, Nika Mansouri-Ghiasi, Konstantina Koliogeorgi, Anirban Nag, Arash Tavakkol, Haiyu Mao, Onur Mutlu, Shai Bergman, Ji Zhang
Hwayong Nam, Seungmin Baek, Jumin Kim, Michael Jaemin Kim, Jung Ho Ahn
Sahil Khan, Abhinav Anand, Kenneth R. Brown, Jonathan M. Baker
Zhixing Jiang, Justin Garrigus, Allison Seigler, Ethan Syed, Yan-Lun Huang, Mehdi Sadi, Tawfik Rahal-Arabi, Lizy Kurian John
Jovan Stojkovic, Abraham Farrell, Zhangxiaowen Gong, Christopher J. Hughes, Josep Torrellas
Eunyeong Cho, Jehyeon Bang, Ranggi Hwang, Minsoo Rhu
Gan Fang, Jianping Zeng, Yuchen Zhou, Changhee Jung
Burak Ocalan, Chloe Alverti, Shashwat Jaiswal, Antonis Psistakis, David A. Koufaty, Suyash Mahar, Steven Swanson, Josep Torrellas
Jingwei Cai, Dehao Kong, Hantao Huang, Zishan Jiang, Zixuan Ma, Qingyu Guo, Zhenxing Zhang, Guiming Shi, Mingyu Gao, Kaisheng Ma, Minghui Yu
Sangpyo Kim, Hyesung Ji, Jongmin Kim, Wonseok Choi, Jaiyoung Park, Jung Ho Ahn
Rohan Basu Roy, Devesh Tiwari
Anshu Gupta, Yingqi Cao, Jason Liang, Yatish Turakhia
Haocheng Lian, Qiyue Zhang, Xinran Zhao, Meichen Dong, Yijie Nie, Zhengyi Zhao, Junzhong Shen, Wei Guo, Chun Huang, Bingcai Sui, Weifeng Liu
Rakesh Nadig, Vamanan Arulchelvan, Mayank Kabra, Harshita Gupta, Rahul Bera, Nika Mansouri-Ghiasi, Nanditha Rao, Qingcai Jiang, Andreas Kosmas Kakolyris, Yu Liang, Mohammad Sadrosadati, Onur Mutlu
"""

# Parse authors per paper
papers = []
for line in hpca2026_raw.strip().split('\n'):
    line = line.strip()
    if not line:
        continue
    authors = [a.strip() for a in line.split(',')]
    papers.append(authors)

# Count per author
author_counts = {}
for paper_authors in papers:
    for a in paper_authors:
        author_counts[a] = author_counts.get(a, 0) + 1

# Known HPCA HoF members (from data.js, normalized names)
hof_members = [
    "Josep Torrellas", "Onur Mutlu", "Nam Sung Kim", "David Brooks",
    "Yan Solihin", "Yuan Xie", "Youtao Zhang", "Jun Yang",
    "Anand Sivasubramaniam", "Rajeev Balasubramonian", "Alper Buyuktosunoglu",
    "Mattan Erez", "Xuehai Qian", "Dean M. Tullsen", "Jung Ho Ahn",
    "William J. Dally", "Stephen W. Keckler", "Tao Li",
    "Vijaykrishnan Narayanan", "Moinuddin K. Qureshi", "Murali Annavaram",
    "Pradip Bose", "Chita R. Das", "Lieven Eeckhout", "Mark D. Hill",
    "Aamer Jaleel", "Mahmut Taylan Kandemir", "John Kim", "Mikko H. Lipasti",
    "Vijay Janapa Reddi", "Gu-Yeon Wei", "David A. Wood", "Huiyang Zhou",
    "Lizy Kurian John", "Tushar Krishna", "Gabriel H. Loh",
    "Scott A. Mahlke", "Margaret Martonosi", "G. Edward Suh", "Guangyu Sun",
    "Carole-Jean Wu", "Amro Awad", "Babak Falsafi", "Ravishankar R. Iyer",
    "Natalie D. Enright Jerger", "Xiaowei Jiang", "Hyesoon Kim",
    "Rakesh Kumar", "Milos Prvulovic", "Minsoo Rhu", "Thomas F. Wenisch",
    "A. Giray Yaglikci", "Brad Calder", "Yiran Chen", "Frederic T. Chong",
    "Michael C. Huang", "Daniel A. Jimenez", "Hai Jin", "Christos Kozyrakis",
    "Donghyuk Lee", "Hsien-Hsin S. Lee", "Hai Helen Li", "Ataberk Olgun",
    "Parthasarathy Ranganathan", "Andre Seznec", "Kevin Skadron",
    "Per Stenstrom", "John B. Carter", "Lizhong Chen", "Adrian Cristal",
    "Reetuparna Das", "Mingyu Gao", "Saugata Ghose", "Boris Grot",
    "Minyi Guo", "Rui Hou", "Benjamin C. Lee", "Xiaofei Liao",
    "Ahmed Louri", "Trevor N. Mudge", "Prashant J. Nair", "David W. Nellans",
    "Mike O'Connor", "Daniel J. Sorin", "Daniel Sanchez", "Lixin Zhang",
    "Jingwen Leng", "Chao Li", "Hai Jin", "Mohammad Sadrosadati",
    "Won Woo Ro", "Changhee Jung", "Jae W. Lee"
]

# Also check common name variants
name_variants = {
    "Moinuddin Qureshi": "Moinuddin K. Qureshi",
    "Moinuddin K. Qureshi": "Moinuddin K. Qureshi",
}

print("=== HPCA 2026 papers by HoF members ===\n")
found = {}
for member in hof_members:
    # Check exact match and common variants
    count = author_counts.get(member, 0)
    if count > 0:
        found[member] = count

# Also search partial matches
for author, count in sorted(author_counts.items(), key=lambda x: -x[1]):
    for member in hof_members:
        last_name = member.split()[-1]
        if last_name in author and author not in found and member not in found:
            # Check more carefully
            if last_name == author.split()[-1]:
                print(f"  PARTIAL MATCH: {author} -> {member}?")

for name, count in sorted(found.items(), key=lambda x: -x[1]):
    print(f"  {name}: {count} paper(s)")

print(f"\nTotal HoF members with HPCA 2026 papers: {len(found)}")
