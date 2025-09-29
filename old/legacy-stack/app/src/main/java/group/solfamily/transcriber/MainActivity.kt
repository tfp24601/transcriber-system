package group.solfamily.transcriber

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import group.solfamily.transcriber.databinding.ActivityMainBinding
import pub.devrel.easypermissions.EasyPermissions

class MainActivity : AppCompatActivity(), EasyPermissions.PermissionCallbacks {
    
    private lateinit var binding: ActivityMainBinding
    
    companion object {
        private const val RC_AUDIO_PERMISSION = 101
        private val REQUIRED_PERMISSIONS = arrayOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.POST_NOTIFICATIONS
        )
    }
    
    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (!isGranted) {
            Toast.makeText(this, "Notification permission is recommended for recording status", Toast.LENGTH_LONG).show()
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupUI()
        checkPermissions()
    }
    
    private fun setupUI() {
        binding.apply {
            btnSingleTest.setOnClickListener {
                testDeepLink("single")
            }
            
            btnMultiTest.setOnClickListener {
                testDeepLink("multi")
            }
            
            btnOpenWeb.setOnClickListener {
                openWebInterface()
            }
            
            btnRequestPermissions.setOnClickListener {
                requestAllPermissions()
            }
        }
        
        updatePermissionStatus()
    }
    
    private fun checkPermissions() {
        if (!EasyPermissions.hasPermissions(this, *REQUIRED_PERMISSIONS)) {
            binding.btnRequestPermissions.visibility = android.view.View.VISIBLE
        }
        
        // Check notification permission for Android 13+
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(
                    this,
                    Manifest.permission.POST_NOTIFICATIONS
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }
    
    private fun requestAllPermissions() {
        EasyPermissions.requestPermissions(
            this,
            "This app needs microphone access to record audio for transcription.",
            RC_AUDIO_PERMISSION,
            *REQUIRED_PERMISSIONS
        )
    }
    
    private fun updatePermissionStatus() {
        val hasAudio = EasyPermissions.hasPermissions(this, Manifest.permission.RECORD_AUDIO)
        binding.tvPermissionStatus.text = if (hasAudio) {
            "✓ Permissions granted. Ready to record!"
        } else {
            "⚠ Microphone permission required"
        }
    }
    
    private fun testDeepLink(mode: String) {
        if (!EasyPermissions.hasPermissions(this, Manifest.permission.RECORD_AUDIO)) {
            Toast.makeText(this, "Please grant microphone permission first", Toast.LENGTH_SHORT).show()
            return
        }
        
        // Simulate deep link call
        val intent = Intent(this, DeepLinkActivity::class.java).apply {
            data = Uri.parse("ssrec://$mode?name=test_recording_${System.currentTimeMillis()}")
        }
        startActivity(intent)
    }
    
    private fun openWebInterface() {
        val intent = Intent(Intent.ACTION_VIEW).apply {
            data = Uri.parse("https://transcriber.solfamily.group")
        }
        startActivity(intent)
    }
    
    override fun onPermissionsGranted(requestCode: Int, perms: MutableList<String>) {
        updatePermissionStatus()
        binding.btnRequestPermissions.visibility = android.view.View.GONE
        Toast.makeText(this, "Permissions granted!", Toast.LENGTH_SHORT).show()
    }
    
    override fun onPermissionsDenied(requestCode: Int, perms: MutableList<String>) {
        updatePermissionStatus()
        Toast.makeText(this, "Some permissions were denied. App may not work properly.", Toast.LENGTH_LONG).show()
        
        if (EasyPermissions.somePermissionPermanentlyDenied(this, perms)) {
            // Show dialog to go to settings
            Toast.makeText(this, "Please enable permissions in Settings", Toast.LENGTH_LONG).show()
        }
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        EasyPermissions.onRequestPermissionsResult(requestCode, permissions, grantResults, this)
    }
}