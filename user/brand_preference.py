#coding:utf-8
import sys
reload(sys)
sys.path.append("..")
sys.setdefaultencoding( "utf-8" )
import torndb
from common.mysql_conf_api import MySQLConfigApi
import datetime
import pickle
import logging
import traceback
import gc
import os
from common.utils import *

def get_goods_brand_info():
    #获取用户下过单的宝贝id
    cmd = "rm -rf data/user_brand_info.txt"
    os.system(cmd)
    user_order_goodsid_list = []
    with open("data/user_order_goodsid.txt", "r") as f:
        user_order_goodsid_list = pickle.load(f)
    #扩展品牌信息
    host, port, user, pwd, db = MySQLConfigApi.get_param_from_ini_file('higo_goods', 0, False)
    db = torndb.Connection(host + ':' + port, db, user, pwd)
    f = open("data/user_brand_info.txt", "w")
    try:
        for goods in user_order_goodsid_list:
            if goods['goods_id'] == None:
                continue
            sql = "select brand_id, brand_name from t_pandora_goods where goods_id=%s" % (goods['goods_id'])
            res = db.query(sql)
            if len(res) == 0:
                continue
            goods['brand_id'] = res[0]['brand_id']
            goods['brand_name'] = res[0]['brand_name']
            if goods['brand_id'] == None:
                continue
            if goods['brand_name'] == None:
                continue
            #action = order
            f.write("%s{\c}%s{\c}%s{\c}%s{\c}order{\c}%s\n" % (goods['uid'], str(goods['goods_id']), str(goods['brand_id']), goods['brand_name'], goods['order_ctime']))
    except Exception, e:
        print e
        print traceback.print_exc()
    finally:
        f.close()
        db.close()
    return

#计算品牌偏好
#preference_weight = action_weight * time_weight * goods_weight
def cal_user_brand_preference():
    cmd = "rm -rf data/user_brand_preference.txt"
    os.system(cmd)
    action_weight = {
    'click' : 1,
    'like': 2,
    'cart' : 5,
    'order' : 10 
    }

    uid_brand_id = {}
    brand_id_2_name_map = {}
    sum_user_brand_id_action_num = {}
    max_brand_id_weight = {}
    f1 = open("data/user_brand_preference.txt", "w")
    with open("data/user_brand_info.txt") as f:
        for line in f:
            if len(line.split("{\c}")) != 6:
                continue
            uid, goods_id, brand_id, brand_name, action,order_ctime = line.strip().split("{\c}")
            if brand_id not in brand_id_2_name_map:
                brand_id_2_name_map[brand_id] = brand_name
            if brand_id not in  max_brand_id_weight:
                max_brand_id_weight[brand_id] = 0
            if uid not in sum_user_brand_id_action_num:
                sum_user_brand_id_action_num.setdefault(uid, {brand_id:0})
                sum_user_brand_id_action_num[uid][brand_id] = 1 * action_weight[action] * cal_time_decay(datetime.datetime.strptime(order_ctime, "%Y-%m-%d"))
            else:
                if brand_id not in sum_user_brand_id_action_num[uid]:
                    sum_user_brand_id_action_num[uid].setdefault(brand_id, 0)
                sum_user_brand_id_action_num[uid][brand_id] += action_weight[action] * cal_time_decay(datetime.datetime.strptime(order_ctime, "%Y-%m-%d"))
            if sum_user_brand_id_action_num[uid][brand_id] > max_brand_id_weight[brand_id] : 
                max_brand_id_weight[brand_id] = sum_user_brand_id_action_num[uid][brand_id]
    #归一化
    for uid, brand_dict in sum_user_brand_id_action_num.items():
        for brand_id, origin_score in brand_dict.items():
            weight = ("%.2f" % (0.01 + (origin_score - 0) / max_brand_id_weight[brand_id]))
            if float(weight) > 1.00 :
                weight = 1.00
            f1.write("%s{\c}%s{\c}%s{\c}%s\n" % (uid, brand_id, brand_id_2_name_map[brand_id], weight))
 
    f1.close()
    return


def main():
    #get_goods_brand_info()
    cal_user_brand_preference()
    return

if __name__ == "__main__":
    main()
