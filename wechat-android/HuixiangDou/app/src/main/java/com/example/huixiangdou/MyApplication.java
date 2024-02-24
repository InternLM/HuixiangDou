package com.example.huixiangdou;

import android.app.Application;
import android.content.Intent;
import android.os.Handler;
import android.util.Log;

public class MyApplication extends Application {

    static final String TAG = MyApplication.class.getName();
    private static MyApplication application;

    private Handler handler = null;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.i(TAG, "myapplication created.");

        application = this;
    }

    public static MyApplication getApplication() {
        return application;
    }

    public void setHandler(Handler handler) {
        this.handler = handler;
    }

    public Handler getHandler() {
        return handler;
    }

}
