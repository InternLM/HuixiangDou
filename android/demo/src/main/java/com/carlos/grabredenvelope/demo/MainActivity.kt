package com.carlos.grabredenvelope.demo

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.Toast
import com.carlos.cutils.base.CBaseAccessibilityActivity

class MainActivity : CBaseAccessibilityActivity() {

    private lateinit var btn: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        initView()
    }

    private fun initView() {
        btn = findViewById(R.id.btn_jump)
        btn.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            Toast.makeText(this@MainActivity, "找到（茴香豆）开启或关闭。", Toast.LENGTH_LONG)
                .show()
        }
    }
}
