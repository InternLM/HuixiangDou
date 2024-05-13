package com.carlos.grabredenvelope.demo

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Rect
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import android.widget.EditText
import android.widget.RelativeLayout
import android.widget.TextView
import android.widget.Toast
import com.carlos.cutils.util.LogUtils
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_EDIT_TEXT
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_GROUP_NAME
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_USER_CONTENT
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_USER_HEADER
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_USER_NAME
import com.carlos.grabredenvelope.demo.WechatConstants.RES_ID_USER_RL
import com.google.gson.Gson
import kotlinx.coroutines.withTimeout
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import java.io.IOException
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.math.abs

data class Query (val type: String, val content: String)
data class UserInfo (val query_id: String, val groupname: String, val username: String, val query: Query)
data class RSP (val code: Int, val state:String, val text:String, val references: ArrayList<String>)
data class QueryResponsePair(val req: UserInfo, val rsp:RSP)
data class ChatResponse(val msg: String, val msgCode: Int, val data: ArrayList<QueryResponsePair>)

class NoDoubleClick(val timeout: Int) {
    var time = 0L

    fun pass(): Boolean {
        var now = System.currentTimeMillis()
        if (time == 0L) {
            time = now
            return true
        }

        if (now - time > this.timeout) {
            time = now
            return true
        }
        return false
    }
}

class SendEmojiService : AccessibilityService() {
    private var groupname: String = ""
    private var lastusername:String = ""
    private var lastcontent:String = ""
    private var firststart = 0L
    private var send_throttle = NoDoubleClick(4000)
    private val WECHAT_PACKAGE = "com.tencent.mm"
    private lateinit var executor: ExecutorService
    private lateinit var httpclient: OkHttpClient
    private var handler = Handler(Looper.getMainLooper())
    private var send_text:String = ""
    private var asked_questions: ArrayList<String> = ArrayList()

    override fun onCreate() {
        super.onCreate()
        LogUtils.d("onCreate")
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        LogUtils.d("onServiceConnected")
        httpclient = OkHttpClient()
        executor = Executors.newSingleThreadExecutor();
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        WechatConstants.setVersion(getAppVersionName(baseContext, WECHAT_PACKAGE))

        when (event.eventType) {
            AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED -> {
                LogUtils.d("通知改变:$event")
            }
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED -> {
                LogUtils.d("界面改变:$event")
            }
            AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED -> {
                LogUtils.d("内容改变:$event")
                // extract latest event in framelayout
                parseSendMessage(event)
            }
        }
    }

    private fun getAppVersionName(context: Context, packageName: String = context.packageName) = try {
        context.packageManager.getPackageInfo(packageName, 0).versionName
    } catch (e: PackageManager.NameNotFoundException) {
        e.printStackTrace()
        ""
    }

    private fun chat_with_server() {
        var userInfo = UserInfo(query_id = groupname, groupname = groupname, username = lastusername, Query(type = "text", content = lastcontent))
        var userJsonStr = Gson().toJson(userInfo)

        var helper = SharedPreferenceHelper(applicationContext)
        var post_url:String = helper.getString("URL", "")

        executor.execute {
            val client = OkHttpClient.Builder().connectTimeout(20, TimeUnit.SECONDS).writeTimeout(40, TimeUnit.SECONDS).readTimeout(180, TimeUnit.SECONDS).build()
            // Define the JSON media type
            val JSON :MediaType? = "application/json; charset=utf-8".toMediaTypeOrNull()

            // Create the request body
            val requestBody = userJsonStr.toRequestBody(JSON)

            // Build the request
            val request = Request.Builder()
                .url(post_url)
                .post(requestBody)
                .build()

            client.newCall(request).enqueue(object : Callback{
                override fun onFailure(call: Call, e: IOException) {
                    Log.e("msg", e.toString())
                }

                override fun onResponse(call: Call, response: Response) {
                    Log.d("msg resp code", response.code.toString())

                    if (response.isSuccessful) {
                        // loop and wait resp
                        var retry: Int = 2
                        while (retry > 0){
                            retry -= 1

                            if (!send_text.equals("")) {
                                var input_and_send = send_text
                                send_text = ""
                                // got set send text
                                Log.d("msg will send", input_and_send)
                                handler.post {
                                    var nodeInfo = rootInActiveWindow.findAccessibilityNodeInfosByViewId(RES_ID_EDIT_TEXT)
                                    if (nodeInfo.size > 0) {
                                        for (et in nodeInfo) {
                                            if (et.className == EditText::class.java.name) {
                                                var args = Bundle()
                                                args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, input_and_send)
                                                et.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
                                            }
                                        }
                                    }
                                }
                                // sleep
                                Thread.sleep(2000)
                                // then click send button
                                if (!send_throttle.pass()) {
                                    Log.d("msg", "click too more")
                                    return
                                }
                                handler.post {
                                    var do_send = click_send()
                                    Log.d("msg", "action send?")
                                    Log.d("msg", do_send.toString())
                                }
                                break
                            }
                            parseRecvMessage()
                            Thread.sleep(5000)
                        }
                        if (retry == 0) {
                            Log.e("msg", "outdate")
                        }

                    } else {
                        Log.d("msg", response.toString())
                    }
                }
            })
        }
    }

    private fun build_reply_text(reply: ChatResponse): String {
        var helper = SharedPreferenceHelper(applicationContext)
        var debug: Boolean = helper.getBoolean("DEBUG", true)

        var sb: StringBuilder = StringBuilder()
        for (item in reply.data) {
            if (debug) {
                sb.append(item.req.query.content)
                sb.append("\n---\n")
                sb.append(item.rsp.code)
                sb.append("\n")
                sb.append(item.rsp.state)
                sb.append("\n")
                sb.append(item.rsp.text)
            } else if (item.rsp.code == 0) {
                sb.append(item.req.query.content)
                sb.append("\n------\n")
                sb.append(item.rsp.text)
            }
        }
        return sb.toString()
    }

    private fun parseRecvMessage() {
        // poll message from server
        var userInfo = UserInfo(query_id = groupname, groupname = groupname, username = lastusername, Query(type = "poll", content = ""))
        var userJsonStr = Gson().toJson(userInfo)

        var helper = SharedPreferenceHelper(applicationContext)
        var url:String = helper.getString("URL", "")
        var post_url:String = url ?: ""

        if (!send_text.equals("")) {
            return
        }

        executor.execute {
            val client = OkHttpClient()
            // Define the JSON media type
            val JSON :MediaType? = "application/json; charset=utf-8".toMediaTypeOrNull()

            // Create the request body
            val requestBody = userJsonStr.toRequestBody(JSON)

            // Build the request
            val request = Request.Builder()
                .url(post_url)
                .post(requestBody)
                .build()

            client.newCall(request).enqueue(object : Callback{
                override fun onFailure(call: Call, e: IOException) {
                    Log.e("msg", e.toString())
                }

                override fun onResponse(call: Call, response: Response) {
                    Log.d("msg resp code", response.code.toString())

                    if (response.isSuccessful) {
                        var reply_text: String = response.body?.string() ?: "response.body?"
                        Log.d("msg parse recv", reply_text)
                        try {
                            var reply: ChatResponse = Gson().fromJson(reply_text, ChatResponse::class.java)
                            if (reply.data.size > 0){
                                send_text = build_reply_text(reply)
                            }
                        } catch (e: Exception){
                            Log.e("msg", e.toString())
                        }

                    } else {
                        Log.e("msg", response.toString())
                    }
                }
            })
        }
    }

    private fun parseWindow() {
        // 声明参数
        var username = ""
        // 获取所有的 rl，看里面的头像位置，头像是 imageview 且为正方形
        var nodeInfo = rootInActiveWindow.findAccessibilityNodeInfosByViewId(RES_ID_USER_RL)
        if (nodeInfo.size < 1){
            Log.d("msg", "no rl found, return")
            return
        }
        var lastTop = -1

        for (rl in nodeInfo) {
            if (rl.className != RelativeLayout::class.java.name) {
                continue
            }

            var rlBound = Rect(0,0,0,0)
            rl.getBoundsInScreen(rlBound)
            if (rlBound.top <= lastTop) {
                // 只处理最下面的 RL
                continue
            }

            var headers = rl.findAccessibilityNodeInfosByViewId(RES_ID_USER_HEADER)
            if (headers.size < 1) {
                continue
            }
            lastTop = rlBound.top

            var header = headers[0]
            var bound = Rect(0,0,0,0)
            header.getBoundsInScreen(bound)
            if (abs(bound.right - bound.left) == abs(bound.bottom - bound.top) && bound.left < 300) {
                // 正方形是头像
                // 头像尺寸显然在屏幕左边，是发送者
                // 获取发送者的名字、发的内容
                var names = rl.findAccessibilityNodeInfosByViewId(RES_ID_USER_NAME)
                if (names.size > 0) {
                    var tv = names[0]
                    if (tv.className == TextView::class.java.name){
                        lastusername = tv.text.toString()
                    }
                }


                var contents = rl.findAccessibilityNodeInfosByViewId(RES_ID_USER_CONTENT)
                if (contents.size > 0) {
                    var tv = contents[0]
                    if (tv.className == TextView::class.java.name){
                        lastcontent = tv.text.toString()
                    }
                }
            }
        }
    }

    private fun parseSendMessage(event: AccessibilityEvent) {
        var classname = event.className.toString()
        var packagename = event.packageName.toString()
        if (classname != "android.widget.LinearLayout" && classname != "android.widget.FrameLayout") return
        if (packagename != "com.tencent.mm") return

        if (firststart == 0L) {
            firststart = System.currentTimeMillis()
            return
        }
        if (System.currentTimeMillis() - firststart < 1000 * 2) {
            // 启动 2 秒内不处理，等 view 稳定
            Log.d("msg", "skip first 2 seconds")
            return
        }

        if (rootInActiveWindow == null) {
            Log.d("msg", "rootInActiveWindow is null")
            return
        }
        // fetch group name
        var nodeInfo = rootInActiveWindow.findAccessibilityNodeInfosByViewId(RES_ID_GROUP_NAME)
        for (tv in nodeInfo) {
            if (tv.className == TextView::class.java.name) {
                var content = tv.text.toString()
                groupname = content
                break
            }
        }

        // 解析发送者和发送内容
        parseWindow()

        nodeInfo = rootInActiveWindow.findAccessibilityNodeInfosByViewId(RES_ID_USER_NAME)
        if (nodeInfo.size < 1) {
            // 单聊
            // 单聊没有 RES_ID_USERNAME，需要把 groupname assign 成 username
            lastusername = groupname
        }
        // 检查要发的内容是否跟之前重复，重复的句子不会请求服务器
        Log.d("send", groupname)
        Log.d("send", lastusername)
        Log.d("send", lastcontent)

        for (question in asked_questions) {
            if (question.equals(lastcontent)) {
                Log.w("msg", "this question already asked")
                return
            }
        }
        asked_questions.add(lastcontent)
        Toast.makeText(application.applicationContext, lastcontent, Toast.LENGTH_SHORT)
        chat_with_server()
    }

    private fun click_send(): Boolean {
        var do_send = false
        val accessibilityNodeInfos =
            rootInActiveWindow?.findAccessibilityNodeInfosByText("发送") ?: return false
        for (accessibilityNodeInfo in accessibilityNodeInfos) {
            do_send = true
            accessibilityNodeInfo.performAction(AccessibilityNodeInfo.ACTION_CLICK)
        }
        return do_send
    }

    override fun onInterrupt() {
        LogUtils.d("onInterrupt")
    }

    override fun onDestroy() {
        super.onDestroy()
        LogUtils.d("onDestroy")
    }
}
