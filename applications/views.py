# ------------------------------
# ライブラリ
# ------------------------------
import csv
import json
import math
import urllib
import zipfile
from io import BytesIO,StringIO
import requests
from django.shortcuts import render
from django.http import JsonResponse,HttpResponseRedirect
from .models import DBModel
from datetime import datetime as dt
import datetime
from django.http import FileResponse
from django.http import HttpResponse



def ajax_proc(request):
	if request.method=='POST':
		print(request.POST)
		post_data={'md_r_day':request.POST.get('r_day'),
							 'md_r_time':request.POST.get('r_time'),
							 'md_r_shisetsu':request.POST.get('r_shisetsu'),
							 'md_r_shitsujou':request.POST.get('r_shitsujou'),
							 'md_r_corder':request.POST.get('r_corder'),}
		# 保存ボタン 01
		if request.POST["db_action"]=="save_01":
			resp_db_action='save'
			BorderDataModel.objects.update_or_create(md_name='border_data_01',defaults=post_data)
			print(f'予約日を登録した 01')
		# 保存ボタン 02
		elif request.POST["db_action"]=="save_02":
			resp_db_action='save'
			BorderDataModel.objects.update_or_create(md_name='border_data_02',defaults=post_data)
			print(f'予約日を登録した 02')
		# 削除ボタン 01
		elif request.POST["db_action"]=="delete_01":
			resp_db_action='delete'
			# データが無いとerrorになるのでtry
			try:
				BorderDataModel.objects.get(md_name='border_data_01').delete()
			except:
				pass
			print(f'予約日を削除した 01')
		# 削除ボタン 02
		elif request.POST["db_action"]=="delete_02":
			resp_db_action='delete'
			# データが無いとerrorになるのでtry
			try:
				BorderDataModel.objects.get(md_name='border_data_02').delete()
			except:
				pass
			print(f'予約日を削除した 02')
		# DBのデータをすべて取得
		try:
			border_data_01=BorderDataModel.objects.get(md_name='border_data_01')
			resp_01={'md_r_day':border_data_01.md_r_day,
										'md_r_time':border_data_01.md_r_time,
										'md_r_shisetsu':border_data_01.md_r_shisetsu,
										'md_r_shitsujou':border_data_01.md_r_shitsujou,
										'md_r_corder':border_data_01.md_r_corder,}
		except:
			resp_01={}
		try:
			border_data_02=BorderDataModel.objects.get(md_name='border_data_02')
			resp_02={'md_r_day':border_data_02.md_r_day,
										'md_r_time':border_data_02.md_r_time,
										'md_r_shisetsu':border_data_02.md_r_shisetsu,
										'md_r_shitsujou':border_data_02.md_r_shitsujou,
										'md_r_corder':border_data_02.md_r_corder,}
		except:
			resp_02={}
		json_resp={'resp_01':resp_01,'resp_02':resp_02,'resp_db_action':resp_db_action}
	return JsonResponse(json_resp)

def userdata(request):
	if request.user.is_authenticated:
		return render(request, 'applications/userdata.html')
	else:
		return HttpResponseRedirect('/accounts/login/')

def ajax_proc_first(request):
	if request.method=='POST':
		# print(request.POST)
		post_data={'req_videoids':request.POST.get('videoids'),
		           }
		# print(post_data)

		client_id = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
		video_id = post_data['req_videoids']
		# print(video_id)

		url = 'https://api.twitch.tv/v5/videos/' + video_id + '/comments?content_offset_seconds=0'
		headers = {'client-id': client_id}
		r = requests.get(url, headers=headers)
		# print(r)
		row_data = r.json()
		# print(row_data)

		# tsとchatを辞書型リストに格納
		ts_chat_dist=[ {'timestamp(JST)':comment['content_offset_seconds'], 'chat':comment['message']['body'] } for comment in row_data['comments'] ]
		# print(ts_chat_dist)

		# DBに保存
		DBModel.objects.update_or_create(
			# ユニークな値
			md_name=video_id,
			# 更新もしくは新規で追加したい値
			defaults={'md_ts_chat':ts_chat_dist}
		)
		print(f'1回目のコメントとTSを登録した')

		json_resp={'ts_chat_dist':ts_chat_dist,
		           'video_id':video_id,
		           'next_token':row_data['_next'],
		           }

	return JsonResponse(json_resp)

def ajax_proc_after(request):
	if request.method=='POST':
		# print(request.POST)
		post_data={
			'req_videoids':request.POST.get('videoids'),
			'req_next_token':request.POST.get('next_token'),
		}
		# print(post_data)

		client_id = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
		video_id = post_data['req_videoids']
		next_token= post_data['req_next_token']
		# print(video_id)

		url = 'https://api.twitch.tv/v5/videos/' + video_id + '/comments?cursor=' + next_token
		headers = {'client-id': client_id}
		r = requests.get(url, headers=headers)
		# print(r)
		row_data = r.json()
		# print(row_data)

		# tsとchatを辞書型リストに格納
		ts_chat_dist=[ {'timestamp(JST)':comment['content_offset_seconds'], 'chat':comment['message']['body'] } for comment in row_data['comments'] ]
		# print(ts_chat_dist)

		# DBに保存
		DBModel.objects.update_or_create(
			# ユニークな値
			md_name=video_id,
			# 更新もしくは新規で追加したい値
			defaults={'md_ts_chat':ts_chat_dist}
		)
		print(f'2回目以降のコメントとTSを登録した')

		try:
			json_resp={'ts_chat_dist':ts_chat_dist,
			           'video_id':video_id,
			           'next_token':row_data['_next'],
			           }
		except:
			json_resp={'ts_chat_dist':ts_chat_dist,
			           'video_id':video_id,
			           'next_token':'None',
			           }

	return JsonResponse(json_resp)




def input_v1(request):
	# ログインの確認
	if request.user.is_authenticated:
		# ページ読み込み時にDBのデータを全て読み込む
		try:
			DB_data=DBModel.objects.all()
			# print(DB_data)
			# finish_list=[ i.md_name for i in DB_data if i.md_dl_state=='finish']
			# videoidに紐づいたタイトルを表示するために変更
			finish_dist=[{'videoid':i.md_name,'title':i.md_video_title} for i in DB_data if i.md_dl_state=='finish']
			# print(finish_list)
		except:
			finish_dist=[]
		json_resp={'finish_dist':finish_dist}
		# print(json_resp)
		# ここでは辞書を返さないとエラーになる
		return render(request,'applications/input_v1.html',json_resp)
	else:
		return HttpResponseRedirect('/accounts/login/')

# DBから逐一辞書を取得する
def ajax_proc_aaa_old_1(request):
	if request.method=='POST':
		# print(request.POST)
		post_data={
			'req_videoids':request.POST.get('videoids'),
			'req_next_token':request.POST.get('next_token'),
			'req_video_length':request.POST.get('video_length'),
			'req_video_recorded_at_jst':request.POST.get('video_recorded_at_jst'),
		}
		# print(post_data)

		client_id = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
		headers = {'client-id': client_id}

		# 1回目はトークンがないので、それを利用してURLを分岐
		if post_data['req_next_token']==None:
			ts_chat_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids'] + '/comments?content_offset_seconds=0'
			# 同じvideoidで再取得するとdistが増え続けるので1回目にDBからvideoidを指定して全て削除
			try:
				DBModel.objects.get(md_name=post_data['req_videoids']).delete()
			except:
				pass
			# 1回目にAPIから動画の長さ(秒)と配信開始日時を取得
			video_data_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids']
			r = requests.get(video_data_url, headers=headers)
			video_data = r.json()
			# print(json.dumps(video_data, indent=2))
			# 動画の長さ(秒)
			video_length = video_data['length']
			# 日時オブジェクトに変換してJSTにするために+9時間
			video_recorded_at_jst=dt.strptime(video_data["recorded_at"],'%Y-%m-%dT%H:%M:%SZ')+datetime.timedelta(hours=9)
		else:
			ts_chat_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids'] + '/comments?cursor=' + post_data['req_next_token']
			# 2回目以降はrequestsから取得
			video_length=post_data['req_video_length']
			video_recorded_at_jst=dt.strptime(post_data['req_video_recorded_at_jst'],'%Y-%m-%d %H:%M:%S')

		# DBからts_chat_distを取得
		try:
			DB_data=DBModel.objects.get(md_name=post_data['req_videoids'])
			# print(DB_data)
			# DBから取得した直後は文字列なのでevalで辞書型リストに変換
			ts_chat_dist_old=eval(DB_data.md_ts_chat)
		# データが無い場合は空
		except:
			ts_chat_dist_old=[]

		# tsとchatを取得
		r = requests.get(ts_chat_url, headers=headers)
		ts_chat_data = r.json()
		# print(ts_chat_data)
		# print(json.dumps(ts_chat_data, indent=2))
		# tsとchatを辞書型リストに格納
		ts_chat_dist=[ {'timestamp(JST)':str(video_recorded_at_jst+datetime.timedelta(seconds=int(comment['content_offset_seconds']))), 'chat':comment['message']['body'] } for comment in ts_chat_data['comments'] ]
		# print(ts_chat_dist)

		# 進捗を計算
		# リストの最後のtsを取得
		last_ts=dt.strptime(ts_chat_dist[-1]['timestamp(JST)'],'%Y-%m-%d %H:%M:%S')-video_recorded_at_jst
		# print(last_ts,video_length)
		# 動画全体の時間から割合を取得して小数点以下切り捨て
		progress=math.floor(int(last_ts.seconds)/int(video_length)*100)
		# print(f'進捗：{progress}%')

		# ajaxに返すレスポンス
		json_resp={'videoids':post_data['req_videoids'],
		           'progress':progress,
		           'video_length':video_length,
		           'video_recorded_at_jst':str(video_recorded_at_jst),
		           }
		# next_tokenの有無でif
		if '_next' in ts_chat_data:
			json_resp['next_token']=ts_chat_data['_next']
			dl_state='pending'
		else:
			json_resp['next_token']='None'
			dl_state='finish'
		# print(json_resp)

		# DBに保存
		DBModel.objects.update_or_create(
			# ユニークな値
			md_name=post_data['req_videoids'],
			# 更新もしくは新規で追加したい値
			defaults={
				'md_ts_chat':ts_chat_dist_old+ts_chat_dist,
				'md_dl_state':dl_state,
			}
		)

	return JsonResponse(json_resp)

# DBから逐一辞書を取得せずpostで送受信する
def ajax_proc_aaa_old_2(request):
	if request.method=='POST':
		# print(request.POST)
		post_data={
			'req_videoids':request.POST.get('videoids'),
			'req_next_token':request.POST.get('next_token'),
			'req_video_length':request.POST.get('video_length'),
			'req_video_recorded_at_jst':request.POST.get('video_recorded_at_jst'),
			'req_ts_chat_dist':request.POST.get('ts_chat_dist'),
		}
		# print(post_data)

		client_id = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
		headers = {'client-id': client_id}

		# 1回目はトークンがないので、それを利用してURLを分岐
		if post_data['req_next_token']==None:
			ts_chat_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids'] + '/comments?content_offset_seconds=0'
			# 同じvideoidで再取得するとdistが増え続けるので1回目にDBからvideoidを指定して全て削除
			try:
				DBModel.objects.get(md_name=post_data['req_videoids']).delete()
			except:
				pass
			# 1回目にAPIから動画の長さ(秒)と配信開始日時を取得
			video_data_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids']
			r = requests.get(video_data_url, headers=headers)
			video_data = r.json()
			# print(json.dumps(video_data, indent=2))
			# 動画の長さ(秒)
			video_length = video_data['length']
			# 日時オブジェクトに変換してJSTにするために+9時間
			video_recorded_at_jst=dt.strptime(video_data["recorded_at"],'%Y-%m-%dT%H:%M:%SZ')+datetime.timedelta(hours=9)
			# 1回目は空のリストを指定
			ts_chat_dist_old=[]
		else:
			ts_chat_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids'] + '/comments?cursor=' + post_data['req_next_token']
			# 2回目以降はrequestsから取得
			video_length=post_data['req_video_length']
			video_recorded_at_jst=dt.strptime(post_data['req_video_recorded_at_jst'],'%Y-%m-%d %H:%M:%S')
			# strだけど中身は辞書型のリストなのでevalで変換
			ts_chat_dist_old=eval(post_data['req_ts_chat_dist'])

		# tsとchatを取得
		r = requests.get(ts_chat_url, headers=headers)
		ts_chat_data = r.json()
		# print(ts_chat_data)
		# print(json.dumps(ts_chat_data, indent=2))
		# tsとchatを辞書型リストに格納
		ts_chat_dist=[ {'timestamp(JST)':str(video_recorded_at_jst+datetime.timedelta(seconds=int(comment['content_offset_seconds']))), 'chat':comment['message']['body'] } for comment in ts_chat_data['comments'] ]
		ts_chat_dist=ts_chat_dist_old+ts_chat_dist
		# print(ts_chat_dist)

		# 進捗を計算
		# リストの最後のtsを取得
		last_ts=dt.strptime(ts_chat_dist[-1]['timestamp(JST)'],'%Y-%m-%d %H:%M:%S')-video_recorded_at_jst
		# print(last_ts,video_length)
		# 動画全体の時間から割合を取得して小数点以下切り捨て
		progress=math.floor(int(last_ts.seconds)/int(video_length)*100)
		# print(f'進捗：{progress}%')

		# ajaxに返すレスポンス
		json_resp={'videoids':post_data['req_videoids'],
		           'progress':progress,
		           'video_length':video_length,
		           'video_recorded_at_jst':str(video_recorded_at_jst),
		           # 辞書型のリストで送信すると勝手に他の型に変換されて使えなくなるので、strでそのままの型で送信してevalした
		           'ts_chat_dist':str(ts_chat_dist),
		           }

		# next_tokenの有無でif
		if '_next' in ts_chat_data:
			json_resp['next_token']=ts_chat_data['_next']
		else:
			json_resp['next_token']='None'
			# すべて取得が完了したらDBに保存
			DBModel.objects.update_or_create(
				# ユニークな値
				md_name=post_data['req_videoids'],
				# 更新もしくは新規で追加したい値
				defaults={
					'md_ts_chat':ts_chat_dist,
					'md_dl_state':'finish',
				}
			)

		# print(json_resp)
		print(json_resp['videoids'])
		print(json_resp['progress'])

	return JsonResponse(json_resp)

# DBから逐一辞書を取得せずpostで送受信する
# タイムスタンプを秒だけにした
def ajax_proc_aaa_old_3(request):
	if request.method=='POST':
		# print(request.POST)
		post_data={
			'req_videoids':request.POST.get('videoids'),
			'req_next_token':request.POST.get('next_token'),
			'req_video_length':request.POST.get('video_length'),
			'req_ts_chat_dist':request.POST.get('ts_chat_dist'),
		}
		# print(post_data)

		client_id = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
		headers = {'client-id': client_id}

		# 1回目はトークンがないので、それを利用してURLを分岐
		if post_data['req_next_token']==None:
			ts_chat_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids'] + '/comments?content_offset_seconds=0'
			# 同じvideoidで再取得するとdistが増え続けるので1回目にDBからvideoidを指定して全て削除
			try:
				DBModel.objects.get(md_name=post_data['req_videoids']).delete()
			except:
				pass
			# 1回目にAPIから動画の長さ(秒)と配信開始日時を取得
			video_data_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids']
			r = requests.get(video_data_url, headers=headers)
			video_data = r.json()
			# print(json.dumps(video_data, indent=2))
			# 動画の長さ(秒)
			video_length = video_data['length']
			# 日時オブジェクトに変換してJSTにするために+9時間
			# video_recorded_at_jst=dt.strptime(video_data["recorded_at"],'%Y-%m-%dT%H:%M:%SZ')+datetime.timedelta(hours=9)
			# 1回目は空のリストを指定
			ts_chat_dist_old=[]
		else:
			ts_chat_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids'] + '/comments?cursor=' + post_data['req_next_token']
			# 2回目以降はrequestsから取得
			video_length=post_data['req_video_length']
			# video_recorded_at_jst=dt.strptime(post_data['req_video_recorded_at_jst'],'%Y-%m-%d %H:%M:%S')
			# strだけど中身は辞書型のリストなのでevalで変換
			ts_chat_dist_old=eval(post_data['req_ts_chat_dist'])

		# tsとchatを取得
		r = requests.get(ts_chat_url, headers=headers)
		ts_chat_data = r.json()
		# print(ts_chat_data)
		# print(json.dumps(ts_chat_data, indent=2))
		# tsとchatを辞書型リストに格納
		# tsは小数点以下も含まれるので切り捨て
		ts_chat_dist=ts_chat_dist_old+[{'ts':math.floor(int(comment['content_offset_seconds'])),'chat':comment['message']['body']} for comment in ts_chat_data['comments']]
		# print(ts_chat_dist)

		# 進捗を計算
		# リストの最後のtsを取得
		last_ts=ts_chat_dist[-1]['ts']
		# print(last_ts,video_length)
		# 動画全体の時間から割合を取得して小数点以下切り捨て
		progress=math.floor(int(last_ts)/int(video_length)*100)
		# print(f'進捗：{progress}%')

		# ajaxに返すレスポンス
		json_resp={'videoids':post_data['req_videoids'],
		           'progress':progress,
		           'video_length':video_length,
		           # 辞書型のリストで送信すると勝手に他の型に変換されて使えなくなるので、strでそのままの型で送信してevalした
		           'ts_chat_dist':str(ts_chat_dist),
		           }

		# next_tokenの有無でif
		if '_next' in ts_chat_data:
			json_resp['next_token']=ts_chat_data['_next']
		else:
			json_resp['next_token']='None'
			# すべて取得が完了したらDBに保存
			DBModel.objects.update_or_create(
				# ユニークな値
				md_name=post_data['req_videoids'],
				# 更新もしくは新規で追加したい値
				defaults={
					'md_ts_chat':ts_chat_dist,
					'md_dl_state':'finish',
				}
			)

		# print(json_resp)
		print(json_resp['videoids'])
		print(json_resp['progress'])

	return JsonResponse(json_resp)

# DBから逐一辞書を取得せずpostで送受信する
# タイムスタンプを秒だけにした→hh:mm:ssの形式にした
def ajax_proc_aaa(request):
	if request.method=='POST':
		# print(request.POST)
		post_data={
			'req_videoids':request.POST.get('videoids'),
			'req_next_token':request.POST.get('next_token'),
			'req_video_length':request.POST.get('video_length'),
			'req_ts_chat_dist':request.POST.get('ts_chat_dist'),
		}
		# print(post_data)

		# 本来はもうAPIを使用してアーカイブのコメントは取得できないが、Twitch自身のclient_idを使用することで現在でも取得可能だがグレーな方法
		# https://ja.stackoverflow.com/questions/83617/twitch-api-を用いてアーカイブ動画のコメントを取得したい
		client_id = 'kimne78kx3ncx6brgo4mv6wki5h1ko'
		headers = {'client-id': client_id}

		# 1回目はトークンがないので、それを利用してURLを分岐
		if post_data['req_next_token']==None:
			ts_chat_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids'] + '/comments?content_offset_seconds=0'
			# 同じvideoidで再取得するとdistが増え続けるので1回目にDBからvideoidを指定して全て削除
			try:
				DBModel.objects.get(md_name=post_data['req_videoids']).delete()
			except:
				# ない場合は何もしない
				pass
			# 1回目のみAPIから諸データを取得
			video_data_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids']
			r = requests.get(video_data_url, headers=headers)
			video_data = r.json()
			# print(json.dumps(video_data, indent=2))
			# 長さ(秒)
			video_length=video_data['length']
			# 1回目は空のリストを指定
			ts_chat_dist_old=[]
			# タイトルは処理で使用しないので先にDBに保存
			DBModel.objects.update_or_create(
				# ユニークな値
				md_name=post_data['req_videoids'],
				# 更新もしくは新規で追加したい値
				defaults={
					'md_video_title':video_data['title'],
				}
			)
		else:
			ts_chat_url = 'https://api.twitch.tv/v5/videos/' + post_data['req_videoids'] + '/comments?cursor=' + post_data['req_next_token']
			# 2回目以降はrequestsから取得
			video_length=post_data['req_video_length']
			# strだけど中身は辞書型のリストなのでevalで変換
			ts_chat_dist_old=eval(post_data['req_ts_chat_dist'])

		# tsとchatを取得
		r = requests.get(ts_chat_url, headers=headers)
		ts_chat_data = r.json()
		# print(ts_chat_data)
		# print(json.dumps(ts_chat_data, indent=2))
		# tsとchatを辞書型リストに格納
		# tsは小数点以下も含まれることがあるので切り捨て
		# 経過時間をhh:mm:ss形式に変換
		ts_chat_dist=ts_chat_dist_old+[{'ts':str(datetime.timedelta(seconds=math.floor(int(comment['content_offset_seconds'])))),'chat':comment['message']['body']} for comment in ts_chat_data['comments'] ]
		# print(ts_chat_dist)

		# 進捗を計算
		# リストの最後のtsを取得
		# hh:mm:ss形式のstrを変換して総秒数を算出
		last_ts_hhmmss=dt.strptime(ts_chat_dist[-1]['ts'],'%H:%M:%S')
		last_ts=last_ts_hhmmss.hour*60*60+last_ts_hhmmss.minute*60+last_ts_hhmmss.second
		# print(last_ts)
		# 動画全体の時間から割合を取得して小数点以下切り捨て
		progress=math.floor(int(last_ts)/int(video_length)*100)
		# print(f'進捗：{progress}%')

		# ajaxに返すレスポンス
		json_resp={'videoids':post_data['req_videoids'],
		           'progress':progress,
		           'video_length':video_length,
		           # 辞書型のリストで送信すると勝手に他の型に変換されて使えなくなるので、strでそのままの型で送信してevalした
		           'ts_chat_dist':str(ts_chat_dist),
		           }

		# next_tokenの有無でif
		if '_next' in ts_chat_data:
			json_resp['next_token']=ts_chat_data['_next']
		else:
			json_resp['next_token']='None'
			# すべて取得が完了したらDBに保存
			DBModel.objects.update_or_create(
				# ユニークな値
				md_name=post_data['req_videoids'],
				# 更新もしくは新規で追加したい値
				defaults={
					'md_ts_chat':ts_chat_dist,
					'md_dl_state':'finish',
				}
			)

		# print(json_resp)
		print(json_resp['videoids'])
		print(json_resp['progress'])

	return JsonResponse(json_resp)

# 保存・削除・プレビュー
def ajax_proc_dd(request):
	if request.method=='POST':
		# print(request.POST)
		# print(request.body)

		# saveかつvideoidが空でない
		if (request.POST.get('db_action')=='save') and (request.POST.getlist('videoids')):
			# 書き込むzipファイルの準備
			# https://www.memory-lovers.blog/entry/2017/06/25/180052
			memory_file=BytesIO() #エラーなし
			# res_zip=StringIO() #TypeError string argument expected, got 'bytes'
			# res_zip = HttpResponse(content_type='application/zip') #予期しない型
			zip_file=zipfile.ZipFile(memory_file,'w')

			for videoid in request.POST.getlist('videoids'):
				# DBからvideoidで検索してts_chat_distを取得
				DB_data=DBModel.objects.get(md_name=videoid)
				# print(DB_data)
				# DBから取得した直後は文字列なのでevalで辞書型リストに変換
				ts_chat_dist=eval(DB_data.md_ts_chat)

				# csv作成、zipにまとめる
				csv_file=HttpResponse(content_type='text/csv')
				# csv_file=BytesIO() #TypeError: a bytes-like object is required, not 'str'
				writer=csv.DictWriter(csv_file,['ts','chat'])
				writer.writeheader()
				writer.writerows(ts_chat_dist)
				# print(csv_file.getvalue())
				# zipにまとめる
				zip_file.writestr(f'{videoid}.csv',csv_file.getvalue())
				csv_file.close()

			# zipファイルの内容をreponseに設定
			zip_file.close() #ここでcloseしないとエラー発生して解凍できない
			response=HttpResponse(memory_file.getvalue(), content_type='application/zip')
			# videoidを,で区切ってファイル名にする
			response['Content-Disposition']=f'attachment; filename="{",".join(request.POST.getlist("videoids"))}.zip"'

			return response

		# deleteの場合、andでrequest.POST.getlist('videoids')すると削除できない
		elif request.POST.get('db_action')=='delete':
			for videoid in request.POST.getlist("videoids[]"):
				DBModel.objects.get(md_name=videoid).delete()
				pass

			# ajaxに返すレスポンス
			json_resp={'videoids':request.POST.getlist("videoids[]"),
			           }
			print(json_resp)

			return JsonResponse(json_resp)

		# previewページを表示させる
		elif request.POST.get('db_action')=='preview' and request.POST.getlist('videoids'):
			# videoidごとのts_chat_distとタイトルを辞書型リストで返す
			json_resp=[{'videoid':videoid,'ts_chat_dist':eval(DBModel.objects.get(md_name=videoid).md_ts_chat),'title':DBModel.objects.get(md_name=videoid).md_video_title} for videoid in request.POST.getlist('videoids')]
			# print(videoid_ts_chat_dist)
			return render(request,'applications/preview_v1.html',{'json_resp':json_resp})

		# 何もしないので204を返す
		else:
			return HttpResponse(status=204)