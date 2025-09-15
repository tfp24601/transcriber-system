package group.solfamily.transcriber

import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import io.tus.java.client.TusClient
import io.tus.java.client.TusUpload
import io.tus.java.client.TusUploader
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File
import java.net.URL
import java.util.concurrent.TimeUnit

class UploadService : Service() {
    
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(5, TimeUnit.MINUTES)
        .build()
    
    companion object {
        private const val UPLOAD_NOTIFICATION_ID = 1002
        private const val BASE_URL = "https://transcriber.solfamily.group"
    }
    
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val mode = intent?.getStringExtra("mode") ?: "single"
        val name = intent?.getStringExtra("name") ?: "recording"
        val source = intent?.getStringExtra("source") ?: "android-bridge"
        
        serviceScope.launch {
            uploadRecording(mode, name, source)
        }
        
        return START_NOT_STICKY
    }
    
    override fun onBind(intent: Intent?): IBinder? = null
    
    private suspend fun uploadRecording(mode: String, name: String, source: String) {
        try {
            // Get the recorded file
            val prefs = getSharedPreferences("recordings", MODE_PRIVATE)
            val filePath = prefs.getString("last_recording", null) ?: return
            val file = File(filePath)
            
            if (!file.exists()) {
                showUploadError("Recording file not found")
                return
            }
            
            showUploadProgress("Starting upload...")
            
            // Try TUS upload first, fallback to direct upload
            val success = uploadWithTus(file, mode, name, source) || 
                         uploadDirect(file, mode, name, source)
            
            if (success) {
                showUploadSuccess()
                // Clean up the local file
                file.delete()
            } else {
                showUploadError("Upload failed")
            }
            
        } catch (e: Exception) {
            showUploadError("Upload error: ${e.message}")
        } finally {
            stopSelf()
        }
    }
    
    private fun uploadWithTus(file: File, mode: String, name: String, source: String): Boolean {
        return try {
            val tusClient = TusClient()
            tusClient.uploadCreationURL = URL("$BASE_URL/uploads")
            tusClient.enableResuming(null)  // Enable resuming without store
            
            val upload = TusUpload(file).apply {
                metadata = mapOf(
                    "filename" to file.name,
                    "mode" to mode,
                    "name" to name,
                    "source" to source
                )
            }
            
            val uploader = tusClient.resumeOrCreateUpload(upload)
            uploader.chunkSize = 1024 * 1024 // 1MB chunks
            
            // Upload with progress
            do {
                val bytesUploaded = uploader.upload()
                val progress = (uploader.offset.toFloat() / file.length() * 100).toInt()
                showUploadProgress("Uploading... $progress%")
            } while (bytesUploaded > -1 && !uploader.finished)
            
            uploader.finished
            
        } catch (e: Exception) {
            false
        }
    }
    
    private fun uploadDirect(file: File, mode: String, name: String, source: String): Boolean {
        return try {
            val requestBody = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart(
                    "file",
                    file.name,
                    file.asRequestBody("audio/mpeg".toMediaTypeOrNull())
                )
                .addFormDataPart("mode", mode)
                .addFormDataPart("name", name)
                .addFormDataPart("source", source)
                .build()
            
            val request = Request.Builder()
                .url("$BASE_URL/ingest")
                .post(requestBody)
                .build()
            
            val response = client.newCall(request).execute()
            response.isSuccessful
            
        } catch (e: Exception) {
            false
        }
    }
    
    private fun showUploadProgress(message: String) {
        val notification = NotificationCompat.Builder(this, "recording_channel")
            .setContentTitle("📤 Uploading Recording")
            .setContentText(message)
            .setSmallIcon(android.R.drawable.stat_sys_upload)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
        
        try {
            NotificationManagerCompat.from(this).notify(UPLOAD_NOTIFICATION_ID, notification)
        } catch (e: SecurityException) {
            // Ignore if notification permission not granted
        }
    }
    
    private fun showUploadSuccess() {
        val notification = NotificationCompat.Builder(this, "recording_channel")
            .setContentTitle("✅ Upload Complete")
            .setContentText("Recording uploaded successfully")
            .setSmallIcon(android.R.drawable.stat_sys_upload_done)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setAutoCancel(true)
            .build()
        
        try {
            NotificationManagerCompat.from(this).notify(UPLOAD_NOTIFICATION_ID, notification)
        } catch (e: SecurityException) {
            // Ignore if notification permission not granted
        }
    }
    
    private fun showUploadError(error: String) {
        val notification = NotificationCompat.Builder(this, "recording_channel")
            .setContentTitle("❌ Upload Failed")
            .setContentText(error)
            .setSmallIcon(android.R.drawable.stat_notify_error)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()
        
        try {
            NotificationManagerCompat.from(this).notify(UPLOAD_NOTIFICATION_ID, notification)
        } catch (e: SecurityException) {
            // Ignore if notification permission not granted
        }
    }
}