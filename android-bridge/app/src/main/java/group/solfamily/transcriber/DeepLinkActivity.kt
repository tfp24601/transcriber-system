package group.solfamily.transcriber

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import group.solfamily.transcriber.databinding.ActivityDeepLinkBinding
import kotlinx.coroutines.launch

class DeepLinkActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityDeepLinkBinding
    private var recordingService: RecordingService? = null
    private var recordingMode: String = "single"
    private var recordingName: String = ""
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDeepLinkBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupUI()
        handleDeepLink()
    }
    
    private fun setupUI() {
        binding.apply {
            btnStartRecording.setOnClickListener {
                startRecording()
            }
            
            btnStopRecording.setOnClickListener {
                stopRecording()
            }
            
            btnCancel.setOnClickListener {
                cancelAndExit()
            }
        }
    }
    
    private fun handleDeepLink() {
        intent?.data?.let { uri ->
            recordingMode = uri.host ?: "single"
            recordingName = uri.getQueryParameter("name") ?: generateDefaultName()
            
            binding.apply {
                tvMode.text = if (recordingMode == "single") {
                    "👤 Single Speaker Mode"
                } else {
                    "👥 Multi Speaker Mode"
                }
                tvRecordingName.text = "Name: $recordingName"
            }
            
            // Auto-start recording after a brief delay
            binding.root.postDelayed({
                startRecording()
            }, 1000)
        }
    }
    
    private fun generateDefaultName(): String {
        val timestamp = java.text.SimpleDateFormat("yyyyMMddHHmmss", java.util.Locale.getDefault())
            .format(java.util.Date())
        return "recording_$timestamp"
    }
    
    private fun startRecording() {
        binding.apply {
            tvStatus.text = "🔴 Recording..."
            btnStartRecording.isEnabled = false
            btnStopRecording.isEnabled = true
            progressBar.visibility = android.view.View.VISIBLE
        }
        
        // Start the recording service
        val serviceIntent = Intent(this, RecordingService::class.java).apply {
            putExtra("mode", recordingMode)
            putExtra("name", recordingName)
        }
        startForegroundService(serviceIntent)
        
        Toast.makeText(this, "Recording started", Toast.LENGTH_SHORT).show()
    }
    
    private fun stopRecording() {
        binding.apply {
            tvStatus.text = "⏹ Stopping and uploading..."
            btnStopRecording.isEnabled = false
            tvProgress.text = "Processing audio file..."
        }
        
        // Stop the recording service
        val serviceIntent = Intent(this, RecordingService::class.java)
        stopService(serviceIntent)
        
        // Start upload process
        startUpload()
    }
    
    private fun startUpload() {
        lifecycleScope.launch {
            try {
                binding.tvProgress.text = "Uploading to server..."
                
                // Start upload service
                val uploadIntent = Intent(this@DeepLinkActivity, UploadService::class.java).apply {
                    putExtra("mode", recordingMode)
                    putExtra("name", recordingName)
                    putExtra("source", "android-bridge")
                }
                startService(uploadIntent)
                
                // For now, simulate upload completion
                binding.root.postDelayed({
                    uploadComplete()
                }, 3000)
                
            } catch (e: Exception) {
                binding.tvProgress.text = "Upload failed: ${e.message}"
                Toast.makeText(this@DeepLinkActivity, "Upload failed", Toast.LENGTH_LONG).show()
            }
        }
    }
    
    private fun uploadComplete() {
        binding.apply {
            tvStatus.text = "✅ Upload complete!"
            tvProgress.text = "Redirecting to web interface..."
            progressBar.visibility = android.view.View.GONE
        }
        
        // Open web interface
        binding.root.postDelayed({
            openWebInterface()
        }, 2000)
    }
    
    private fun openWebInterface() {
        val intent = Intent(Intent.ACTION_VIEW).apply {
            data = Uri.parse("https://transcriber.solfamily.group")
        }
        startActivity(intent)
        finish()
    }
    
    private fun cancelAndExit() {
        // Stop any ongoing recording
        val serviceIntent = Intent(this, RecordingService::class.java)
        stopService(serviceIntent)
        
        finish()
    }
}