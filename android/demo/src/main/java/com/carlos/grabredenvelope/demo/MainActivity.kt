package com.carlos.grabredenvelope.demo

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.text.Editable
import android.widget.Button
import android.widget.EditText
import android.widget.Switch
import android.widget.Toast
import com.carlos.cutils.base.CBaseAccessibilityActivity
import com.google.android.material.switchmaterial.SwitchMaterial

class MainActivity : CBaseAccessibilityActivity() {

    private lateinit var btn_jump: Button
    private lateinit var btn_url: Button
    private lateinit var et_url: EditText
    private lateinit var sw_debug: SwitchMaterial

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        initView()
    }

    private fun initView() {
        btn_jump = findViewById(R.id.btn_jump)
        et_url = findViewById(R.id.et_url)
        sw_debug = findViewById(R.id.sw_debug)

        var helper = SharedPreferenceHelper(applicationContext)

        var default_url = et_url.text.toString()
        var get_saved_url: String = helper.getString("URL", default_url)
        et_url.text = Editable.Factory.getInstance().newEditable(get_saved_url)

        btn_jump.setOnClickListener {
            var debug = sw_debug.isChecked()
            helper.saveBoolean("DEBUG", debug)

            var url: String = helper.getString("URL", "")
            if (url.isEmpty()) {
                Toast.makeText(this@MainActivity, "请确认 URL 正确，点击确定！", Toast.LENGTH_LONG).show()
            } else {
                startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                Toast.makeText(this@MainActivity, "找到（茴香豆）开启或关闭。", Toast.LENGTH_LONG)
                    .show()
            }

        }

        btn_url = findViewById(R.id.btn_url)
        btn_url.setOnClickListener {
            var url = et_url.text.toString()
            var helper = SharedPreferenceHelper(applicationContext)
            helper.saveString("URL", url)

            Toast.makeText(this@MainActivity, "修改成功", Toast.LENGTH_LONG)
                .show()
        }
    }
}
