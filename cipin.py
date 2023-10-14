import json
path = "./cipin/"
textlen = 0
def from_text(text):
    for i in range(len(text)):
        if dic.get(text[i]) != None:
            dic[text[i]] += 1
        else:
            dic[text[i]] = 1
        if i == len(text)-1:
            break
        if dic.get(text[i:i+1]) != None:
            dic[text[i:i+1]] += 1
        else:
            dic[text[i:i+1]] = 1
        if i == len(text)-2:
            break
        if dic.get(text[i:i+2]) != None:
            dic[text[i:i+2]] += 1
        else:
            dic[text[i:i+2]] = 1

dic = {}
for i in range(9):
    print(i)
    text = ""
    with open(path+f"{i}.txt","r") as f:
        text = f.read()
        textlen += len(text)
    from_text(text)

single_freq = {}

pro_freq = {}
letter = "abcdefghijklmnopqrstuvwxyz"
for i in letter:
    single_freq[i] = ((dic.get(i) if dic.get(i) != None else 0)+1)/(textlen+26)

for i in letter:
    for j in letter:
        for k in letter:
            pro_freq[f"{k}|{i}{j}"] = ((dic.get(i+j+k) if dic.get(i+j+k) != None else 0)+1)/((dic.get(i+j) if dic.get(i+j) != None else 0)+26)


with open("single_freq.json","w") as f:
    f.write(json.dumps(single_freq))

with open("pro_freq.json","w") as f:
    f.write(json.dumps(pro_freq))
