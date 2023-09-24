# 导入库——qq邮箱测试，其他邮箱略有差异
import poplib
import time
import os
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
import re
import pickle
import pandas as pd
import datetime
# 输入邮件地址, 口令和POP3服务器地址:
email_user = 'ruanfen2023@163.com'

# 此处密码是授权码,用于登录第三方邮件客户端
password = 'HENQXYVQONXWALQU'

pop3_server = 'pop.163.com'


class student:
    def __init__(self, student_id, student_name, student_mail):
        self.student_id = student_id
        self.student_name = student_name
        self.mail = student_mail
        self.score = {}
        self.submit = {}

student_list = {}
wrongdict = {}
# 授权码登录邮箱
def email_login(email_user, password):
    # 连接到POP3服务器,有些邮箱服务器需要ssl加密，可以使用poplib.POP3_SSL
    server = poplib.POP3("pop.163.com")

    # server=poplib.POP3(pop3_server,110,timeout=10)
    # 可以打开或关闭调试信息
    #server.set_debuglevel(1)

    # 身份认证:
    server.user(email_user)
    server.pass_(password)

    # 返回邮件数量和占用空间:
    print('Messages: %s. Size: %s' % server.stat())

    # list()返回所有邮件的编号:
    resp, mails, octets = server.list()

    return mails, server

def decode_str(str_in):
    """字符编码转换"""
    value, charset = decode_header(str_in)[0]
    if charset:
        value = value.decode(charset)
    return value

def Subjectprocess(Subject):
    def num_to_chinese(num):
        num_dict = {
            "1": "一", "2": "二", "3": "三", "4": "四", "5": "五",
            "6": "六", "7": "七", "8": "八", "9": "九", "10": "十"
        }
        return num_dict.get(str(num), str(num))
    pattern = r"(\d{10})[_\s-]([\u4e00-\u9fa5]+)[_\s-]软分第([1一二三四五六七八九十\d]+)次作业"
    match = re.match(pattern, Subject)
    if match:   
        student_id = match.group(1)
        student_name = match.group(2)
        assignment_num = match.group(3)
        if assignment_num.isdigit():
            assignment_num = num_to_chinese(assignment_num)
        unified_str = f"{student_id}-{student_name}-软分第{assignment_num}次作业"
        return unified_str, assignment_num
    else:
        return "wrong text", 0

def try_add_student(filename, email):
    pattern = r"(\d{10})[_\s-]([\u4e00-\u9fa5]+)[_\s-]软分第([1一二三四五六七八九十\d]+)次作业"
    match = re.match(pattern, filename)
    if match:   
        student_id = match.group(1)
        student_name = match.group(2)
        assignment_num = match.group(3)
        if student_id not in student_list.keys():
            student_list[student_id] = student(student_id, student_name, email)    
        elif student_list[student_id].submit[assignment_num] == "yes":
            return "已经提交过了"
        elif student_list[student_id].submit[assignment_num] == "scored":
            return "已经提交过了"
        student_list[student_id].submit[assignment_num] = "yes"
        return "提交成功"


def try_parse_wrong(wrongSubject, filename, email):
    print("错误的邮件主题:"+wrongSubject)
    print("错误的文件名:"+filename)
    student_id = input("请输入其学号:")
    student_name = input("请输入其姓名:")
    assignment_num = input("请输入其作业次数:")
    if student_id not in student_list.keys():
        student_list[student_id] = student(student_id, student_name, email)
    student_list[student_id].submit[assignment_num] = "yes"
    return f"{student_id}-{student_name}-软分第{assignment_num}次作业"

def save_att_file(msg, save_path, Subject, email, wrongSubject=""):
    """附件下载函数"""
    def add_extension_from_a_to_b(a, b):
    # 获取a的文件后缀
        _, a_extension = os.path.splitext(a)
        
        # 将a的后缀添加到b上
        new_b = f"{b}{a_extension}"
        
        return new_b

    for part in msg.walk():
        file_name = part.get_filename()
        # contentType = part.get_content_type()
        attachment_files =[]
        if file_name:
            file_name = decode_str(file_name)
            data =  part.get_payload(decode=True)
            # print("emailcontent:\r\n"+data.decode('unicode_escape'))
            if Subject == "wrong text":
                new_file_name, _ = Subjectprocess(file_name)
                if new_file_name == "wrong text":
                    new_file_name = try_parse_wrong(wrongSubject, file_name, email)    
                else:
                    try_add_student(new_file_name, email)
                att_file = open(os.path.join(save_path, add_extension_from_a_to_b(file_name, new_file_name)), 'wb')
                wrongdict[wrongSubject] = add_extension_from_a_to_b(file_name, new_file_name)
            else:
                add_homework = try_add_student(Subject, email)
                if add_homework == "已经提交过了":
                    continue
                att_file = open(os.path.join(save_path, add_extension_from_a_to_b(file_name, Subject)), 'wb')
                
            attachment_files.append(file_name)
            att_file.write(data)
            att_file.close()
            print(f"附件 {file_name} 下载完成")

def readmail(homeworkid):
    # 遍历所有邮件
    mails,server = email_login(email_user,password)
    if not os.path.exists(os.path.join("./homework/"+homeworkid)):
        os.mkdir(os.path.join("./homework/"+homeworkid))
    for i in range(4,len(mails)+1):
        resp,lines,octets = server.retr(i)
        
        msg_content=b'\r\n'.join(lines).decode('unicode_escape')

        # 解析邮件:
        msg = Parser().parsestr(msg_content)
        #print(msg)

        From = parseaddr(msg.get('from'))[1]#发件人
        To = parseaddr(msg.get('To'))[1]#收件人
        Cc = parseaddr(msg.get_all('Cc'))[1]#抄送人
        Subject = decode_str(parseaddr(msg.get('Subject'))[1])#主题
       
        # 获取邮件时间,格式化收件时间
        date1 = time.strptime(msg.get("Date")[0:24],'%a, %d %b %Y %H:%M:%S')
        # 邮件时间格式转换
        date2 = time.strftime("%Y-%m-%d %H:%M:%S",date1)
        """ if date2 <= "2022-09-18":
            continue

        print(Subject)
        print(date2)
        break """
        print(f'发件人：{From}；收件人：{To}；抄送人：{Cc}；主题：{Subject}；收件日期：{date2}')

        # 主题和日期验证所需邮件
        newSubject, thisid = Subjectprocess(Subject)
        if newSubject == "wrong text":
            if Subject in wrongdict:
                continue
            else:
                save_att_file(msg, './homework/'+homeworkid, newSubject, From, Subject)
        elif thisid == homeworkid:
            save_att_file(msg, './homework/'+homeworkid, newSubject, From)


# 登录获取邮件列表
def save_csv(homeworkid):
    assignments = [homeworkid]  # 假设只有一次作业，可以添加更多

# 准备一个空的 DataFrame
    columns = ['学号', '姓名'] + assignments
    df = pd.DataFrame(columns=columns)

    # 填充 DataFrame
    for student_id, student_obj in student_list.items():
        row = {'学号': student_obj.student_id, '姓名': student_obj.student_name}
        for assignment in assignments:
            if student_obj.submit.get(assignment) == 'scored':
                row[assignment] = student_obj.score.get(assignment, '')
        df = df.append(row, ignore_index=True)

    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    filename = f"scores_for_assignment_{homeworkid}_{now}.csv"
    df.to_csv(filename.format(homeworkid, ), index=False, encoding='utf-8')
def Scoring(homeworkid):
    for student_id in sorted(student_list.keys()):
        if student_list[student_id].submit[homeworkid] == "yes":
            input_score = input(f"请输入{student_list[student_id].student_id},{student_list[student_id].student_name}的分数:")
            if input_score == "q":
                return
            else:
                student_list[student_id].score[homeworkid] = input_score
                student_list[student_id].submit[homeworkid] = "scored"
    save_csv(homeworkid)
    return
if os.path.exists("./student_list.pkl"):
    student_list = pickle.load(open("./student_list.pkl", "rb"))
if os.path.exists("./wrongdict.pkl"):
    wrongdict = pickle.load(open("./wrongdict.pkl", "rb"))

readmail("一")
Scoring("一")
# 下载主程序

pickle.dump(student_list, open("./student_list.pkl", "wb"))
pickle.dump(wrongdict, open("./wrongdict.pkl", "wb"))

