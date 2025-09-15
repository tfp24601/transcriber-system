# iOS Shortcuts Setup Guide

This guide will help you create iOS Shortcuts for recording audio and uploading it to your transcriber system.

## Prerequisites

- iOS device with Shortcuts app (pre-installed on iOS 12+)
- Microphone permissions granted to Shortcuts app
- Access to `https://transcriber.solfamily.group`

## Shortcut 1: Quick Dictate (Single Speaker)

### Steps to Create:

1. **Open Shortcuts app**
2. **Tap "+" to create new shortcut**
3. **Add the following actions in order:**

#### Action 1: Get Text from Input
- Add: "Get Text from Input"
- Input Type: Text
- Default Answer: (leave blank)
- Prompt: "Recording name (optional)"

#### Action 2: Set Variable
- Add: "Set Variable" 
- Variable Name: `RecordingName`
- Value: Text from "Get Text from Input"

#### Action 3: Get Current Date
- Add: "Get Current Date"

#### Action 4: Format Date
- Add: "Format Date"
- Date: Current Date
- Format: Custom
- Custom Format: `yyyyMMddHHmmss`

#### Action 5: If Statement
- Add: "If"
- Condition: "RecordingName" "Has Any Value"
- If True: Use RecordingName
- If False: Use formatted date

#### Action 6: Set Variable (Final Name)
- Add: "Set Variable"
- Variable Name: `FinalName`
- Value: Result from If statement

#### Action 7: Record Audio
- Add: "Record Audio"
- Quality: Normal or High
- Start Recording Immediately: Yes
- Finish Recording: On Tap

#### Action 8: Set Variable (Audio File)
- Add: "Set Variable"
- Variable Name: `AudioFile`
- Value: Recorded Audio

#### Action 9: Get URLs from Text
- Add: "Get URLs from Text"
- Text: `https://transcriber.solfamily.group/ingest`

#### Action 10: Get Contents of URL (Upload)
- Add: "Get Contents of URL"
- URL: URL from previous step
- Method: POST
- Request Body: Form
- Form Fields:
  - `file`: AudioFile (File)
  - `mode`: `single` (Text)
  - `name`: FinalName (Text)  
  - `source`: `ios-shortcut` (Text)

#### Action 11: Get Value for JSON
- Add: "Get Value for" 
- Dictionary: Contents of URL
- Key: `job_id`

#### Action 12: Set Variable (Job ID)
- Add: "Set Variable"
- Variable Name: `JobID`
- Value: Value for job_id

#### Action 13: Get URLs from Text (View URL)
- Add: "Get URLs from Text"
- Text: `https://transcriber.solfamily.group/view?id=` + JobID

#### Action 14: Open URLs
- Add: "Open URLs"
- URLs: URLs from previous step

4. **Configure shortcut settings:**
   - Name: "Quick Dictate"
   - Icon: Microphone
   - Color: Green
   - Use with Siri: Yes
   - Siri Phrase: "Quick dictate"

5. **Save the shortcut**

## Shortcut 2: Quick Meeting (Multi Speaker)

Follow the same steps as above, but change:
- **Action 10**: Change `mode` field from `single` to `multi`
- **Shortcut Name**: "Quick Meeting"
- **Icon Color**: Blue
- **Siri Phrase**: "Quick meeting"

## Web Integration URLs

Your web app should link to these shortcuts using:

### Single Mode Link:
```
shortcuts://run-shortcut?name=Quick%20Dictate&x-success=https%3A//transcriber.solfamily.group/view%3Fid%3DPLACEHOLDER&x-error=https%3A//transcriber.solfamily.group/%3Ferror%3Dshortcut_failed
```

### Multi Mode Link:
```
shortcuts://run-shortcut?name=Quick%20Meeting&x-success=https%3A//transcriber.solfamily.group/view%3Fid%3DPLACEHOLDER&x-error=https%3A//transcriber.solfamily.group/%3Ferror%3Dshortcut_failed
```

## Advanced Configuration

### Adding Authentication (Future)

When Cloudflare Access is integrated, you'll need to modify the shortcuts to include authentication:

1. Add "Get Contents of URL" action before the upload
2. URL: `https://transcriber.solfamily.group/auth/token`
3. Store the JWT token in a variable
4. Add Headers to the upload request:
   - `Authorization: Bearer [JWT Token]`

### Error Handling

Add these actions after the upload:

1. **If Statement**: Check if upload was successful
2. **Show Notification**: Display success/error message
3. **Get Contents of URL**: Check job status periodically

### Background Recording

The shortcuts support background recording by default, but for best results:
- Keep the Shortcuts app active during recording
- Avoid switching apps frequently
- Ensure sufficient battery and storage

## Troubleshooting

### Common Issues:

1. **Recording fails**: Check microphone permissions
2. **Upload fails**: Verify network connection and transcriber.solfamily.group accessibility
3. **Shortcut not triggered**: Ensure Siri phrases are unique and clearly spoken

### Testing:

1. Test each shortcut manually first
2. Try with Siri voice commands
3. Test from web app button integration
4. Verify recordings appear in transcriber history

### Logs:

Check the Shortcuts app's "Run History" for detailed error information.

## Security Notes

- Shortcuts have access to recorded audio
- Audio is uploaded over HTTPS
- No audio data is stored locally after upload
- Consider device security (lock screen, etc.)

## Performance Tips

- Use Wi-Fi for faster uploads
- Keep recordings under 90 minutes
- Close other apps during long recordings
- Ensure adequate storage space

## Integration with Web App

The web app detects iOS devices and shows appropriate UI:
- Large recording buttons
- Platform-specific instructions
- Fallback to file upload if shortcuts unavailable

Your shortcuts are now ready to use with the transcriber system!