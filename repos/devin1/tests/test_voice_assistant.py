"""
test_voice_assistant.py
------------------------
This file contains unit and integration tests for the Devin Voice Assistant module. 
The tests validate the functionality of wake word detection, speaker verification, 
voice command recognition, and system integrations (PC, mobile, and other OS).

The goal is to ensure error-free performance, compatibility across devices, 
and full functionality in controlling PCs and other OS environments.
"""

import unittest
from unittest.mock import patch, MagicMock
from modules.voice_assistant.wake_word_detection import WakeWordDetector
from modules.voice_assistant.speaker_verification import SpeakerVerifier
from modules.voice_assistant.voice_recognition import VoiceRecognizer
from modules.voice_assistant.pc_integration import PCIntegration
from modules.voice_assistant.mobile_integration import MobileIntegration
from modules.voice_assistant.otheros_integration import OtherOSIntegration
from modules.voice_assistant.voice_profile import VoiceProfileManager

class TestWakeWordDetection(unittest.TestCase):
    def setUp(self):
        self.detector = WakeWordDetector(wake_word="Hey Devin")

    def test_wake_word_detected(self):
        with patch.object(self.detector, 'detect', return_value=True) as mock_detect:
            result = self.detector.detect("Hey Devin")
            self.assertTrue(result)
            mock_detect.assert_called_once_with("Hey Devin")

    def test_wake_word_not_detected(self):
        with patch.object(self.detector, 'detect', return_value=False) as mock_detect:
            result = self.detector.detect("Hello Devin")
            self.assertFalse(result)
            mock_detect.assert_called_once_with("Hello Devin")

class TestSpeakerVerification(unittest.TestCase):
    def setUp(self):
        self.verifier = SpeakerVerifier()

    def test_speaker_verified(self):
        with patch.object(self.verifier, 'verify', return_value=True) as mock_verify:
            result = self.verifier.verify("sample_audio_path")
            self.assertTrue(result)
            mock_verify.assert_called_once_with("sample_audio_path")

    def test_speaker_not_verified(self):
        with patch.object(self.verifier, 'verify', return_value=False) as mock_verify:
            result = self.verifier.verify("sample_audio_path")
            self.assertFalse(result)
            mock_verify.assert_called_once_with("sample_audio_path")

class TestVoiceRecognition(unittest.TestCase):
    def setUp(self):
        self.recognizer = VoiceRecognizer()

    def test_command_recognition(self):
        with patch.object(self.recognizer, 'recognize', return_value="Open Browser") as mock_recognize:
            result = self.recognizer.recognize("audio_path")
            self.assertEqual(result, "Open Browser")
            mock_recognize.assert_called_once_with("audio_path")

    def test_unrecognized_command(self):
        with patch.object(self.recognizer, 'recognize', return_value=None) as mock_recognize:
            result = self.recognizer.recognize("audio_path")
            self.assertIsNone(result)
            mock_recognize.assert_called_once_with("audio_path")

class TestPCIntegration(unittest.TestCase):
    def setUp(self):
        self.pc_integration = PCIntegration()

    def test_execute_pc_command(self):
        with patch.object(self.pc_integration, 'execute_command', return_value=True) as mock_execute:
            result = self.pc_integration.execute_command("Open File Explorer")
            self.assertTrue(result)
            mock_execute.assert_called_once_with("Open File Explorer")

class TestMobileIntegration(unittest.TestCase):
    def setUp(self):
        self.mobile_integration = MobileIntegration()

    def test_execute_mobile_command(self):
        with patch.object(self.mobile_integration, 'execute_command', return_value=True) as mock_execute:
            result = self.mobile_integration.execute_command("Open Camera")
            self.assertTrue(result)
            mock_execute.assert_called_once_with("Open Camera")

class TestOtherOSIntegration(unittest.TestCase):
    def setUp(self):
        self.otheros_integration = OtherOSIntegration()

    def test_execute_otheros_command(self):
        with patch.object(self.otheros_integration, 'execute_command', return_value=True) as mock_execute:
            result = self.otheros_integration.execute_command("Launch Terminal")
            self.assertTrue(result)
            mock_execute.assert_called_once_with("Launch Terminal")

class TestVoiceProfileManager(unittest.TestCase):
    def setUp(self):
        self.profile_manager = VoiceProfileManager()

    def test_enroll_voice_profile(self):
        with patch.object(self.profile_manager, 'enroll', return_value=True) as mock_enroll:
            result = self.profile_manager.enroll("sample_audio_path")
            self.assertTrue(result)
            mock_enroll.assert_called_once_with("sample_audio_path")

    def test_verify_voice_profile(self):
        with patch.object(self.profile_manager, 'verify', return_value=True) as mock_verify:
            result = self.profile_manager.verify("sample_audio_path")
            self.assertTrue(result)
            mock_verify.assert_called_once_with("sample_audio_path")

    def test_delete_voice_profile(self):
        with patch.object(self.profile_manager, 'delete', return_value=True) as mock_delete:
            result = self.profile_manager.delete("user_id")
            self.assertTrue(result)
            mock_delete.assert_called_once_with("user_id")

if __name__ == "__main__":
    unittest.main()
