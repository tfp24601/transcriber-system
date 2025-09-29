package group.solfamily.transcriber

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.media.MediaRecorder
import android.os.IBinder
import android.os.PowerManager
import androidx.core.app.NotificationCompat
import java.io.File
import java.io.IOException

class RecordingService : Service() {
    
    private var mediaRecorder: MediaRecorder? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private var recordingFile: File? = null
    private var recordingMode: String = "single"
    private var recordingName: String = ""
    
    companion object {
        private const val NOTIFICATION_ID = 1001
        private const val CHANNEL_ID = "recording_channel"
        private const val CHANNEL_NAME = "Recording Service"
    }
    
    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        acquireWakeLock()
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        recordingMode = intent?.getStringExtra("mode") ?: "single"
        recordingName = intent?.getStringExtra("name") ?: "recording_${System.currentTimeMillis()}"
        
        startForeground(NOTIFICATION_ID, createNotification())
        startRecording()
        
        return START_STICKY
    }
    
    override fun onDestroy() {
        stopRecording()
        releaseWakeLock()
        super.onDestroy()
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    private fun createNotificationChannel() {
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                CHANNEL_NAME,
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Shows recording status"
                setShowBadge(false)
            }
            
            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }
    
    private fun createNotification(): Notification {
        val stopIntent = Intent(this, RecordingService::class.java).apply {
            action = "STOP_RECORDING"
        }
        val stopPendingIntent = PendingIntent.getService(
            this, 0, stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        
        val mode = if (recordingMode == "single") "👤 Single" else "👥 Multi"
        
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("🎙️ Recording - $mode")
            .setContentText("Tap to stop: $recordingName")
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .addAction(
                android.R.drawable.ic_media_pause,
                "Stop",
                stopPendingIntent
            )
            .build()
    }
    
    private fun acquireWakeLock() {
        val powerManager = getSystemService(POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            "TranscriberBridge::RecordingWakeLock"
        )
        wakeLock?.acquire(30 * 60 * 1000L) // 30 minutes max
    }
    
    private fun releaseWakeLock() {
        wakeLock?.let {
            if (it.isHeld) {
                it.release()
            }
        }
    }
    
    private fun startRecording() {
        try {
            // Create output file
            val audioDir = File(filesDir, "audio")
            if (!audioDir.exists()) {
                audioDir.mkdirs()
            }
            
            recordingFile = File(audioDir, "$recordingName.wav")
            
            // Initialize MediaRecorder
            mediaRecorder = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.S) {
                MediaRecorder(this)
            } else {
                @Suppress("DEPRECATION")
                MediaRecorder()
            }
            
            mediaRecorder?.apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setAudioSamplingRate(16000) // 16kHz for better transcription
                setAudioEncodingBitRate(64000) // 64kbps
                setOutputFile(recordingFile?.absolutePath)
                
                prepare()
                start()
            }
            
        } catch (e: IOException) {
            e.printStackTrace()
            stopSelf()
        }
    }
    
    private fun stopRecording() {
        mediaRecorder?.let { recorder ->
            try {
                recorder.stop()
                recorder.release()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
        mediaRecorder = null
        
        // File is now ready for upload
        recordingFile?.let { file ->
            if (file.exists()) {
                // Store file path for upload service
                getSharedPreferences("recordings", MODE_PRIVATE).edit()
                    .putString("last_recording", file.absolutePath)
                    .putString("last_mode", recordingMode)
                    .putString("last_name", recordingName)
                    .apply()
            }
        }
    }
}