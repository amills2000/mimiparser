import re
import json
import hashlib
import os
import pandas as pd
import argparse

def get_mimi_type(filename):
    #extract the mimikatz type using the regular expression #\s(\w+::[^\r\n]+) to match mimikatz(powershell) # sekurlsa:\:ekeys
    with open(filename, 'r') as file:
        filedata = file.read()
        mimi_type = re.search(r'#\s(\w+::[^ \r\n]+)', filedata)
        if mimi_type:
            return mimi_type.group(1)
        else:
            return None

def get_mimi_data_sekurlsa(filename):
    credenctials = []
    cred = {}
    head = True
    parent_group= None
    sub_group= None
    try:
        with open(filename, 'r') as file:
            while True:
                line = file.readline()
                if not line:
                    credenctials.append(cred)
                    break
                if line.startswith('Authentication Id'):
                    head = False
                    if cred=={}: #if cred is empty
                        pass
                    elif cred["User Name"].startswith("UMFD") or cred["User Name"].startswith("DWM"):
                        cred = {}
                        parent_group= None
                        sub_group= None
                    else:
                        credenctials.append(cred)
                        cred = {}
                        parent_group= None
                        sub_group= None
                if head:
                    continue
                if not(line.startswith(" ")):
                    result = re.search(r'([^:]+):([^\n\r]+)', line)
                    if result:
                        cred[result.group(1).strip()] = result.group(2).strip()
                        continue
                if line.startswith(" "):
                    result = re.search(r'^\s+([^\s\*:]+)\s:[\r\n]+', line)
                    if result:
                        parent_group= result.group(1)
                        cred[parent_group] = {}
                        continue
                    result = re.search(r'\[\d+\] Primary', line)
                    if result:
                        continue
                    result = re.search(r'\*\s(\w+)\s+:\s([^\r\n]+)', line)
                    if result:
                        if parent_group!=None:
                            cred[parent_group][result.group(1).strip()] = result.group(2).strip()
                        else:
                            if not("sub" in cred):
                                cred["sub"] = {}
                                parent_group = "sub"
                            cred[parent_group][result.group(1).strip()] = result.group(2).strip()
                        continue
                    result = re.search(r'\*\s([^:]+):[\r\n]+', line)
                    if result:
                        sub_group= result.group(1).strip()
                        if parent_group!=None:
                            cred[parent_group][sub_group] = {}
                        else:
                            if not("sub" in cred):
                                cred["sub"] = {}
                                parent_group = "sub"
                            cred[parent_group][sub_group] = {}
                        continue
                    result = re.search(r'\s+(\w+)\s+([^\r\n]+)', line)
                    if result:
                        if parent_group!=None:
                            cred[parent_group][sub_group][result.group(1).strip()] = result.group(2).strip()
                        else:
                            if not("sub" in cred):
                                cred["sub"] = {}
                                parent_group = "sub"
                            cred[parent_group][sub_group][result.group(1).strip()] = result.group(2).strip()
                        continue
    except Exception as e:
        print(e)
    return credenctials

def get_mimi_data_dcsync(filename):
    credenctials = []
    cred = {}
    head = True
    parent_group= None
    sub_group= None
    try:
        with open(filename, 'r') as file:
            while True:
                line = file.readline()
                if not line:
                    credenctials.append(cred)
                    break
                if line.startswith('SAM Username'):
                    head = False
                    if cred=={}: #if cred is empty
                        pass
                    else:
                        credenctials.append(cred)
                        cred = {}
                        parent_group= None
                        sub_group= None
                if head:
                    continue
                if not(line.startswith(" ") or line.startswith("*")):
                    result = re.search(r'([^:]+):([^\n\r]+)', line)
                    if result:
                        cred[result.group(1).strip()] = result.group(2).strip()
                        continue
                    result = re.search(r'([^:]+):[\n\r]+', line)
                    if result:
                        parent_group= result.group(1).strip()
                        sub_group= None
                        continue
                if line.startswith("* "):
                    result= re.search(r'\*\s+([^\*\r\n]+)', line)
                    if result:
                        sub_group = result.group(1).strip()
                        if not (parent_group in cred):
                            cred[parent_group] = {}
                        cred[parent_group][sub_group] = {}
                        continue

                if line.startswith(" "):
                    if parent_group==None:
                        continue
                    result = re.search(r'\s+([^\*:]+):([^\r\n]+)', line)
                    result2 = re.search(r'\s+(\d+)\s+([^\r\n]+)', line)
                    result=result or result2
                    if sub_group==None:
                        if not (parent_group in cred):
                            cred[parent_group] = {}
                        if result:
                            cred[parent_group][result.group(1).strip()] = result.group(2).strip()
                            continue
                    else:
                        if not (parent_group in cred):
                            cred[parent_group] = {}
                        if not (sub_group in cred[parent_group]):
                            cred[parent_group][sub_group] = {}
                        if result:
                            cred[parent_group][sub_group][result.group(1).strip()] = result.group(2).strip()
                            continue     
    except Exception as e:
        print(e)
    return credenctials

def get_mimi_data_trusts(filename):
    credenctials = []
    cred = {}
    head = True
    current_domain = None
    domain= None
    try:
        with open(filename, 'r') as file:
            while True:
                line = file.readline()
                if not line:
                    #credenctials.append(cred)
                    break
                if line.startswith('Current domain'):
                    head = False
                    result= re.search(r'Current domain:\s+([^\s]+)\s+\(([^\s]+)\s+\/([^\)]+)', line)
                    if result:
                        current_domain = (result.group(1).strip(),result.group(2).strip(),result.group(3).strip())
                        continue
                if head:
                    continue
                if line.startswith('Domain'):
                    result= re.search(r'Domain:\s+([^\s]+)\s+\(([^\s]+)\s+\/([^\)]+)', line)
                    if result:
                        domain = (result.group(1).strip(),result.group(2).strip(),result.group(3).strip())
                        continue
                if line.startswith(' ['):
                    result=re.search(r'\s+\[\s*([^\s]+)\s*\]\s+([^\s]+)\s+\-\>\s+([^\s\r\n]+)',line)
                    if result:
                        if cred!={}:
                            credenctials.append(cred)
                            cred = {}
                        direction = result.group(1).strip()
                        source = result.group(2).strip()
                        target = result.group(3).strip()
                        cred["direction"] = direction
                        cred["source"] = source
                        cred["target"] = target
                        cred["current_domain_name"] = current_domain[0]
                        cred["current_domain_alias"] = current_domain[1]
                        cred["current_domain_sid"] = current_domain[2]
                        cred["trust_domain_name"] = domain[0]
                        cred["trust_domain_alias"] = domain[1]
                        cred["trust_domain_sid"] = domain[2]
                if re.match(r'^\s+\*',line):
                    result=re.search(r'^\s+\*\s+([^\s]+)\s+([A-Za-s0-9]+)$',line)
                    if result:
                        cred[result.group(1).strip()] = result.group(2).strip()   
    except Exception as e:
        print(e)
    return credenctials

def mimikatz_cheker(filename):
    #check if file contains mimikatz on it
    with open(filename, 'r') as file:
        filedata = file.read()
        if 'mimikatz' in filedata:
            return True
        else:
            return False

def mimikatz_finder(directory):
    #find all files that contains mimikatz
    files = []
    for filename in os.listdir(directory):
        try:
            if os.path.isfile(directory+"/"+filename) and mimikatz_cheker(directory+"/"+filename):
                files.append(filename)
        except:
            pass
    return files

def update_checker(dir,filename):
    if not os.path.isfile(dir+"/files.json"):
        return False
    with open(dir+"/"+filename, 'r') as file:
        #compute hash
        filedata = file.read()
        hash = hashlib.md5(filedata.encode()).hexdigest()
        #check if hash is in the list of hashes
        with open(dir+"/files.json", 'r') as file:
            data = json.load(file)
            if hash in data and data[hash]["filename"]==filename:
                #check if file out in csvs folder
                if os.path.isfile("csvs/"+filename.split(".")[0]+".csv"):
                    return True
                else:
                    return False
            else:
                return False

def normalize_json(data: dict) -> dict: 
    new_data = {}
    for key, value in data.items(): 
        if not isinstance(value, dict): 
            new_data[key] = value 
        else: 
            for k, v in value.items(): 
                if not isinstance(v, dict): 
                    new_data[key + "_" + k] = v
                else:
                    for k1, v1 in v.items():
                        new_data[key + "_" + k + "_" + k1] = v1
    return new_data 

def normalize_json_array(data):
    new_data = []
    for item in data:
        new_data.append(normalize_json(item))
    return new_data

def store_results(dir,credentials,filename,mimi_type,force_overwrite):
    if not os.path.isdir(dir+"/csvs"):
        os.mkdir(dir+"/csvs")
    dest_folder=""
    if mimi_type.startswith("sekurlsa"):
        dest_folder=dir+"/csvs/csvs_sekurlsa/"
    if mimi_type.startswith("lsadump::dcsync"):
        dest_folder=dir+"/csvs/csvs_dcsync/"
    if mimi_type.startswith("lsadump::trust"):
        dest_folder=dir+"/csvs/csvs_trust/"
    if dest_folder=="":
        dest_folder=dir+"/csvs/csvs_unknown/"
    #check if csvs folder exists
    if not os.path.isdir(dest_folder):
        os.mkdir(dest_folder)
    #check if jsons folder exists
    if not os.path.isdir(dir+"/jsons"):
        os.mkdir(dir+"/jsons")
    #create files.json if it does not exist
    if not os.path.isfile(dir+"/files.json"):
        with open(dir+"/files.json", 'w') as file:
            json.dump({}, file)
    name=filename.split(".")[0]
    #check if file name exists
    if os.path.isfile(dest_folder+name+".csv") and force_overwrite=="False":
        #prompt user actions: overwrite, rename, skip
        while True:
            print("File "+filename+".csv already exists")
            print("1. Overwrite")
            print("2. Rename")
            print("3. Skip")
            choice = input("Enter choice: ")
            match choice:
                case "1":
                    break
                case "2":
                    i = 1
                    while os.path.isfile(dest_folder+name+"("+str(i)+").csv"):
                        i+=1
                    old_filename = filename
                    filename = name+"("+str(i)+")."+filename.split(".")[1]
                    #rename original file 
                    os.rename(dir+"/"+old_filename, dir+"/"+filename)
                    print("File renamed to "+name+"("+str(i)+").csv")
                    name=filename.split(".")[0]
                    break
                case "3":
                    print("File skipped")
                    return
                case _:
                    print("Invalid choice")
    #store credentials in csv file
    df = pd.DataFrame(normalize_json_array(credentials))
    df = df.drop_duplicates(subset=[col for col in df.columns if not col in ["Logon Time","Session","Authentication Id"]])
    #add mimikatz type as columns 
    df["mimikatz_type"] = mimi_type
    df.to_csv(dest_folder+name+".csv", index=False)
    #store credentials in json file
    with open(dir+"/jsons/"+name+".json", 'w') as file:
        json.dump(credentials, file)
    #store hash in files.json
    with open(dir+"/files.json", 'r') as file:
        data = json.load(file)
        with open(dir+"/"+filename, 'r') as file:
            #compute hash
            filedata = file.read()
            hash = hashlib.md5(filedata.encode()).hexdigest()
            data[hash]={}
            data[hash]["filename"] = filename
            data[hash]["mimi_type"] = mimi_type
    with open(dir+"/files.json", 'w') as file:
        json.dump(data, file)
        
def unify_results(dir):
    #find all folders starting with csvs_
    writer = pd.ExcelWriter(dir+"/mimikatz_credentials.xlsx", engine = 'xlsxwriter')
    folders=[]
    data_folders=[]
    csv_folder=dir+"/csvs/"
    for folder in os.listdir(csv_folder):
        if folder.startswith("csvs_"):
            if folder=="csvs_data":
                data_folders.append((folder,csv_folder+"/"+folder))
                continue
            folders.append((folder,csv_folder+"/"+folder))
    for folder in folders:
        #create one excel sheet for each folder
        files = os.listdir(folder[1])
        if len(files)==0:
            print("No files to unify")
            return
        df = pd.DataFrame()
        for file in files:
            try:
                data = pd.read_csv(folder[1]+"/"+file)
                data["filename"] = file
                df = pd.concat([df,data])
            except Exception as e:
                print("Error reading file "+file)
                print(e)
        df.to_excel(writer, sheet_name=folder[0], index=False)
    for folder in data_folders:
        #create excel_sheet for each file 
        files = os.listdir(folder[1])
        if len(files)==0:
            print("No files to unify")
            return
        for file in files:
            try:
                data = pd.read_csv(folder[1]+"/"+file)
                data["filename"] = file
                data.to_excel(writer, sheet_name=folder[0].replace("csvs_","")+"_"+file.split(".")[0], index=False)
            except Exception as e:
                print("Error reading file "+file)
                print(e)
    writer.close()

def clean_users_data(file):
    print("Cleaning file "+file)
    #read file
    data = pd.read_csv(file)
    #add row vip_group
    with open("vip_groups.txt", 'r') as file_vip:
        vip_groups = file_vip.readlines()
        vip_groups = [group.strip() for group in vip_groups]
    #add row vip_group	
    data["vip_group"] = False
    #iterate rows
    for index, row in data.iterrows():
        if "memberof" in row and "distinguishedname" in row and isinstance(row["memberof"], str):
            #extract distinguished name parts 
            dname_parts= row["distinguishedname"].split(",")
            #remove CN=
            dname_parts = [part.replace("CN=","") for part in dname_parts]
            #join all parts except part=samaccountname
            domain_parts=[part for part in dname_parts if not part==row["samaccountname"]]
            domain=".".join(domain_parts)
            #extract member of parts
            memberof_parts = row["memberof"].split(",")
            #remove CN=
            memberof_parts = [part.replace("CN=","") for part in memberof_parts]
            #remove part if in domain_parts
            memberof_parts = [part for part in memberof_parts if not part in domain_parts]
            #join all parts
            row["memberof"] = "\n".join(memberof_parts)
            #check if memberof is in vip_groups
            if any(group in vip_groups for group in memberof_parts):
                row["vip_group"] = True
            else:
                row["vip_group"] = False
            #add domain
            row["domain"] = domain
            data.loc[index] = row
    
    #save file
    data.to_csv(file, index=False)
            

def enrich_data(dir):
    userfiles=[]
    if not os.path.isdir(dir+"/data"):
        print("No data directory found")
        return
    #list files on data direcotry
    files = os.listdir(dir+"/data")
    for file in files:    
        #read first line to see headers
        with open(dir+"/data/"+file, 'r') as f:
            headers = f.readline().split(",")
        #remove \" from headers
        headers = [header.replace("\"","").strip() for header in headers]
        #check if headers contain  at least  samaccountname,logoncount,description,objectsid,memberof,samaccounttype,distinguishedname
        if all(elem in headers for elem in ["samaccountname","logoncount","description","objectsid","memberof","samaccounttype","distinguishedname"]):
            if not "vip_group" in headers:
                clean_users_data(dir+"/data/"+file)
            userfiles.append(file)
    users_data=pd.DataFrame()
    for ufile in userfiles:
        #open file and add to dataframe
        users_data = pd.concat([users_data,pd.read_csv(dir+"/data/"+ufile)])
    if not os.path.isdir(dir+"/csvs/csvs_data"):
        os.mkdir(dir+"/csvs/csvs_data")
    users_data.to_csv(dir+"/csvs/csvs_data/users_data.csv", index=False)
    #iterate all csvs and enrich user data by sid
    for folder in os.listdir(dir+"/csvs"):
        if folder.startswith("csvs_"):
            files = os.listdir(dir+"/csvs"+"/"+folder)
            for file in files:
                data = pd.read_csv(dir+"/csvs"+"/"+folder+"/"+file)
                #check which header it contains SID or Object Security ID
                if "SID" in data.columns:
                    #merga data with users_data by SID and add columns
                    data = pd.merge(data, users_data, left_on="SID", right_on="objectsid", how="left")
                    data.to_csv(dir+"/csvs"+"/"+folder+"/"+file, index=False)
                elif "Object Security ID" in data.columns:
                    data = pd.merge(data, users_data, left_on="Object Security ID", right_on="objectsid", how="left")
                    data.to_csv(dir+"/csvs"+"/"+folder+"/"+file, index=False)
        

if __name__ == "__main__":
    #parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-d","--directory", help="directory to search for mimikatz files",required=True)
    parser.add_argument("-f","--force_overwrite", help="force overwrite of files",required=False,default=True)
    args = parser.parse_args()
    #create csv folder if not exists
    if not os.path.isdir(args.directory+"/csvs"):
        os.mkdir(args.directory+"/csvs")
    #find all files that contains mimikatz
    force_overwrite = args.force_overwrite
    files = mimikatz_finder(args.directory)
    #parse all files
    for file in files:
        if not update_checker(args.directory,file):
            mimi_type = get_mimi_type(args.directory+"/"+file)
            if mimi_type==None:
                print("File "+file+" does not contain a valid mimikatz type")
                continue
            mimi_type=mimi_type.lower()
            if mimi_type.startswith("sekurlsa"):
                mimi_data = get_mimi_data_sekurlsa(args.directory+"/"+file)
                store_results(args.directory,mimi_data, file,mimi_type,force_overwrite)
            if mimi_type.startswith("lsadump::dcsync"):
                mimi_data = get_mimi_data_dcsync(args.directory+"/"+file)
                store_results(args.directory,mimi_data, file,mimi_type,force_overwrite)
            if mimi_type.startswith("lsadump::trust"):
                mimi_data = get_mimi_data_trusts(args.directory+"/"+file)
                store_results(args.directory,mimi_data, file,mimi_type,force_overwrite)
        else:
            print("File "+file+" already processed")
    enrich_data(args.directory)
    print("All files processed")
    unify_results(args.directory)
    print("Results unified")