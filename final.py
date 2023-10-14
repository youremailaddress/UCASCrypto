from Crypto.Util.number import *
import json,re,copy,sys
from math import log10

class Settings:
    def __init__(self) -> None:
        self.single_rate = 0.4 # 单因子所占权重
        self.itermax = 10
        self.show = 10 # 最后显示前几个最可能的结果
        self.killline = 0.85 # 每轮删除小于当前最优值多少百分比的所有可能结果
        self.single_freq_path = "./single_freq.json" # 单词频信息文件位置
        self.pro_freq_path = "./pro_freq.json" # 多词频信息文件位置
        self.enc_path = "./encry.txt" # 待解密文件位置
        self.modnum = 26 # 模数
        self.primelis = self._get_primelis() #获取所有 a 可能的取值
        self.keylength = 24 # 自行修改为 Kasiski 预测的最可能取值
        self.mapping = self._build_mapping() # 获取所有可能变换
        self.enc_content = self._read_file_content(self.enc_path)
        self.enc_split = self._split_enc() # 将 enc 根据 keylength 分成若干份
    
    def _read_file_content(self,path):
        return open(path,"r").read()
    
    def _split_enc(self):
        enclis = []
        for i in range(0,len(self.enc_content),self.keylength):
            enclis.append(self.enc_content[i:i+self.keylength])
        return enclis

    def _build_mapping(self):
        '''
        返回所有可能的代换
        '''
        mapping = []
        origin = "abcdefghijklmnopqrstuvwxyz"
        for i in self.primelis:
            for j in range(26):
                res = ""
                for item in origin:
                    res += chr((((ord(item)-97)*i+j)%self.modnum)+97)
                mapping.append(res)
        return mapping

    def _get_primelis(self):
        '''
        获取所有 a 可能的取值
        '''
        lis = []
        for i in range(self.modnum):
            if GCD(i,self.modnum) == 1:
                lis.append(i)
        return lis

    def fetch_single_column(self,columnid):
        '''
        获取 enc 的 columnid 列（从 0 开始）
        '''
        assert columnid < self.keylength
        retlis = []
        for item in self.enc_split:
            try:
                retlis.append(item[columnid])
            except:
                pass
        return retlis
        
def get_max_index(encrydir,num):
    rang="qwertyuiopasdfghjklzxcvbnm"
    g = open(encrydir,"r")
    g.seek(0,0)
    transfer3d = [[[0 for i in rang] for j in rang] for k in rang]
    c = g.read(3)
    while len(c) == 3:
        if c[0] in rang and c[1] in rang and c[2] in rang:
            transfer3d[rang.index(c[0])][rang.index(c[1])][rang.index(c[2])] += 1
        c = g.read(3)
    g.seek(1,0)
    c = g.read(3)
    while len(c) == 3:
        if c[0] in rang and c[1] in rang and c[2] in rang:
            transfer3d[rang.index(c[0])][rang.index(c[1])][rang.index(c[2])] += 1
        c = g.read(3)
    g.seek(2,0)
    c = g.read(3)
    while len(c) == 3:
        if c[0] in rang and c[1] in rang and c[2] in rang:
            transfer3d[rang.index(c[0])][rang.index(c[1])][rang.index(c[2])] += 1
        c = g.read(3)
    mes = []
    for i in rang:
        for j in rang:
            for k in rang:
                if transfer3d[rang.index(i)][rang.index(j)][rang.index(k)]>=num:
                    mes.append((transfer3d[rang.index(i)][rang.index(j)][rang.index(k)],rang.index(i),rang.index(j),rang.index(k)))
    mes.sort(reverse=True)
    if len(mes) == 0:
        print("[fatal]No Enough data")
        exit()
    ret = []
    t = 0
    for i in mes:
        ret.append((rang[i[1]]+rang[i[2]]+rang[i[3]],i[0]))
        t += i[0]
        if t > 5000:
            return ret
    return [(rang[i[1]]+rang[i[2]]+rang[i[3]],i[0]) for i in mes]

def Kasiski(encrydir):
    '''
    优化过的卡西斯基方法寻找维吉尼亚密码可能密钥长度
    '''
    with open(encrydir,"r",encoding="utf-8") as f:
        c = f.read()
        if len(c) < 100:
            print("[fatal]No Enough data")
            exit()
        b = []

        mm = get_max_index(encrydir,len(c)/10000)

        for tex,num in mm:
            t = c.find(tex)
            all_index = [substr.start() for substr in re.finditer(c[t:t+3], c)]
            all_index = [all_index[i]-all_index[i-1] for i in range(1,len(all_index))]
            try:
                b.append([len([0 for i in all_index if not i%n]) for n in range(1,max(all_index)//2)])
            except ValueError:
                pass
        all = [0]*max([(len(i)) for i in b])
        for i in range(len(b)):
            for j in range(len(b[i])):
                all[j] += b[i][j]
        
        all = [all[i]**(1.5)*log10(i)/(all[i-1]+all[i]+all[i+1]+1) for i in range(1,len(all)-1)]

        prob = [(all[i]/sum(all),i+2) for i in range(len(all))]
        prob.sort(reverse=True)
        print(prob[:10])

class Structure:
    def __init__(self,settings:Settings) -> None:
        self.score = 1 #当前变换组合的得分
        self.mappings = [] # 当前变换组合
        self.config = settings
        self.single_freq = self.read_json_from_file(self.config.single_freq_path)
        self.pro_freq = self.read_json_from_file(self.config.pro_freq_path)
    
    def __lt__(self,other):
        return self.score < other.score

    def __str__(self):
        return "mappings:"+'\n'.join(self.mappings)+"\n"+self.decrypt_all()

    def read_json_from_file(self,path):
        '''
        根据 path 读取 json 文件
        '''
        with open(path,"r") as f:
            return json.loads(f.read())

    def calc_freq(self,lis):
        '''
        计算 lis 里的频率，返回字典
        '''
        dic = {}
        for item in lis:
            if dic.get(item) != None:
                dic[item] += 1
            else:
                dic[item] = 1
        for k,v in dic.items():
            dic[k] = v/len(lis)
        return dic
    
    def letter_mapping_back(self,letter,mapping:str):
        '''
        将一个字母根据给定 mapping 转换规则还原为原始字母
        '''
        assert len(letter) == 1
        assert letter in "qwertyuiopasdfghjklzxcvbnm"
        return chr(97+mapping.find(letter))

    def lis_mapping_back(self,lis,mapping:str):
        '''
        将一个加密的 lis 根据给定 mapping 转换规则还原为原始 lis
        '''
        return [self.letter_mapping_back(i,mapping) for i in lis]

    def dic_mapping_back(self,dic,mapping:str):
        '''
        将一个加密的 dic 频率字典根据给定 mapping 转换规则还原为原始频率字典
        '''
        retdic = {}
        for k,v in dic.items():
            retdic[self.letter_mapping_back(k,mapping)] = v
        return retdic

    def calc_dics_relativity(self,dic1,dic2):
        '''
        计算两个 dic 的相似程度 采用余弦相似度算法
        '''
        score = 0
        for i in "qwertyuiopasdfghjklzxcvbnm":
            try:
                score += dic1[i]*dic2[i]
            except:
                pass
        return score
    
    def calc_single(self,mapping):
        '''
        append之前 计算单因子得分
        '''
        whichcolumn = len(self.mappings)
        handle_column = self.config.fetch_single_column(whichcolumn)
        freq_dic = self.calc_freq(handle_column)
        freq_dic_back = self.dic_mapping_back(freq_dic,mapping)
        return self.calc_dics_relativity(freq_dic_back,self.single_freq)
    
    def calc_multi(self,mapping):
        '''
        append之前 计算多因子得分
        '''
        score = 1
        whichcolumn = len(self.mappings)
        prepreviouscolumn = self.config.fetch_single_column(whichcolumn - 2)
        previouscolumn = self.config.fetch_single_column(whichcolumn - 1)
        handle_column = self.config.fetch_single_column(whichcolumn)
        prepreviouscolumn_back = self.lis_mapping_back(prepreviouscolumn,mapping)
        previouscolumn_back = self.lis_mapping_back(previouscolumn,mapping)
        handle_column_back = self.lis_mapping_back(handle_column,mapping)
        for i in range(len(handle_column_back)):
            score *= self.pro_freq[f"{handle_column_back[i]}|{prepreviouscolumn_back[i]}{previouscolumn_back[i]}"]
        return score ** (1/len(handle_column_back))
        
    def append(self,mapping):
        '''
        将当前列的映射加入当前 Structure 中
        '''
        column_single_score = self.calc_single(mapping)
        if len(self.mappings) == 0 or len(self.mappings) == 1: # 如果是前两个，无法使用条件概率验证，因此只使用单因子
            self.score *= column_single_score
            self.mappings.append(mapping)
        else:
            column_multi_score = self.calc_multi(mapping)
            self.score *= self.config.single_rate*column_single_score+(1-self.config.single_rate)*column_multi_score
            self.mappings.append(mapping)

    def decrypt_all(self):
        revert_decrypt_lis = []
        for i in range(self.config.keylength):
            revert_decrypt_lis.append(self.lis_mapping_back(self.config.fetch_single_column(i),self.mappings[i]))
        res = ""
        for m in range(len(revert_decrypt_lis[0])):
            for n in range(len(revert_decrypt_lis)):
                try:
                    res += revert_decrypt_lis[n][m]
                except:
                    pass
        return res

if __name__ == "__main__":
    if len(sys.argv) == 1:
        pass
    elif sys.argv[1] == 'K':
        Kasiski("encry.txt")
        print("Please update keylength in Setting and restart")
    setting = Settings()
    structure_lis = []
    for i in range(len(setting.mapping)):
        structuretmp = Structure(setting)
        structuretmp.append(setting.mapping[i])
        structure_lis.append(structuretmp)
    maxstru = max(structure_lis)
    killline = maxstru.score*setting.killline
    print(killline)
    structure_lis = [item for item in structure_lis if item.score > killline]
    if len(structure_lis) > setting.itermax:
        structure_lis = sorted(structure_lis,key=lambda s:s.score,reverse=True)[:setting.itermax]
    for i in range(setting.keylength-1):
        tmplis = []
        for structure in structure_lis:
            for mapping in setting.mapping:
                tmpstruc = copy.deepcopy(structure)
                tmpstruc.append(mapping)
                tmplis.append(tmpstruc)
        structure_lis = tmplis
        maxstru = max(structure_lis)
        killline = maxstru.score*setting.killline
        print(killline)
        structure_lis = [item for item in structure_lis if item.score > killline]
        if len(structure_lis) > setting.itermax:
            structure_lis = sorted(structure_lis,key=lambda s:s.score,reverse=True)[:setting.itermax]
        print(len(structure_lis))
    structure_lis = sorted(structure_lis,key=lambda s:s.score,reverse=True)[:setting.show]
    print(f"Top {setting.show} results is list here:")
    for item in structure_lis:
        print(item)
    