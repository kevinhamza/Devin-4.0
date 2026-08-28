// src/integrations/holomat_integration.ts — Holomat AR/hand-tracking integration
// Ported from external/Holomat/run.py and home_screen.py
// Provides hand gesture control, MediaPipe integration, AR overlay UI

import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

const DEVIN_ROOT = path.join(__dirname, '../..');
const HOLOMAT_DIR = path.join(DEVIN_ROOT, 'external/Holomat');

// ── Hand tracking (from Holomat/run.py MediaPipe patterns) ───────────────────

export interface HandLandmark {
  x: number;
  y: number;
  z: number;
}

export interface HandDetectionResult {
  detected: boolean;
  handedness: 'Left' | 'Right' | 'Both' | 'None';
  landmarks: HandLandmark[];
  gesture: string;
  confidence: number;
}

export async function detectHandGesture(imagePath: string): Promise<HandDetectionResult> {
  const code = `
import cv2, json, sys, os
os.environ.setdefault('DISPLAY', ':0')
try:
    import mediapipe as mp
    img = cv2.imread("${imagePath}")
    if img is None:
        print(json.dumps({"detected": False, "error": "Cannot open image"}))
        sys.exit(0)
    mp_hands = mp.solutions.hands
    with mp_hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.5) as hands:
        results = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if not results.multi_hand_landmarks:
            print(json.dumps({"detected": False, "handedness": "None", "landmarks": [], "gesture": "none", "confidence": 0}))
        else:
            lms = results.multi_hand_landmarks[0].landmark
            landmarks = [{"x": round(l.x, 4), "y": round(l.y, 4), "z": round(l.z, 4)} for l in lms]
            # Detect basic gestures
            tip_y = [lms[4].y, lms[8].y, lms[12].y, lms[16].y, lms[20].y]
            pip_y = [lms[3].y, lms[6].y, lms[10].y, lms[14].y, lms[18].y]
            fingers_up = sum(1 for i in range(1,5) if tip_y[i] < pip_y[i])
            gesture = "open_hand" if fingers_up >= 4 else "fist" if fingers_up == 0 else "pointing" if fingers_up == 1 else "peace" if fingers_up == 2 else "three_fingers" if fingers_up == 3 else "unknown"
            hand_label = results.multi_handedness[0].classification[0].label if results.multi_handedness else "Right"
            conf = results.multi_handedness[0].classification[0].score if results.multi_handedness else 0.5
            print(json.dumps({"detected": True, "handedness": hand_label, "landmarks": landmarks, "gesture": gesture, "confidence": round(conf, 3)}))
except ImportError:
    print(json.dumps({"detected": False, "error": "mediapipe not installed"}))
except Exception as e:
    print(json.dumps({"detected": False, "error": str(e)[:100]}))
`;
  try {
    const out = cp.execSync(`python3 -c '${code}'`, { encoding: 'utf8', timeout: 15000 }).trim();
    return JSON.parse(out);
  } catch {
    return { detected: false, handedness: 'None', landmarks: [], gesture: 'error', confidence: 0 };
  }
}

// ── Perspective transform (from Holomat/run.py) ───────────────────────────────

export interface TransformPoint {
  x: number;
  y: number;
}

export function applyPerspectiveTransform(
  points: TransformPoint[],
  srcWidth: number,
  srcHeight: number,
  dstWidth: number,
  dstHeight: number,
  imagePath: string,
  outputPath: string
): Promise<string> {
  const code = `
import cv2, numpy as np
pts_src = np.float32([${points.slice(0, 4).map(p => `[${p.x},${p.y}]`).join(',')}])
pts_dst = np.float32([[0,0],[${dstWidth},0],[${dstWidth},${dstHeight}],[0,${dstHeight}]])
M = cv2.getPerspectiveTransform(pts_src, pts_dst)
img = cv2.imread("${imagePath}")
if img is not None:
    warped = cv2.warpPerspective(img, M, (${dstWidth}, ${dstHeight}))
    cv2.imwrite("${outputPath}", warped)
    print("OK")
else:
    print("ERROR:cannot_open_image")
`;
  return new Promise((resolve) => {
    cp.exec(`python3 -c '${code}'`, { timeout: 10000 }, (_err, stdout) => {
      resolve(stdout?.trim() === 'OK' ? outputPath : 'Transform failed');
    });
  });
}

// ── AR overlay (from Holomat/home_screen.py AppCircle patterns) ───────────────

export interface ARApp {
  id: string;
  name: string;
  icon?: string;
  action: () => void | Promise<void>;
}

export interface AROverlay {
  apps: ARApp[];
  screenWidth: number;
  screenHeight: number;
  isVisible: boolean;
}

export function createAROverlay(apps: ARApp[], screenWidth = 1366, screenHeight = 768): AROverlay {
  return { apps, screenWidth, screenHeight, isVisible: false };
}

export function calculateAppPositions(
  overlay: AROverlay
): Array<{ app: ARApp; x: number; y: number; radius: number }> {
  const cx = overlay.screenWidth / 2;
  const cy = overlay.screenHeight / 2;
  const distance = 250;
  const appRadius = 75;
  const count = overlay.apps.length;
  return overlay.apps.map((app, i) => {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2;
    return {
      app,
      x: Math.round(cx + distance * Math.cos(angle)),
      y: Math.round(cy + distance * Math.sin(angle)),
      radius: appRadius,
    };
  });
}

// ── Live camera hand tracking loop ────────────────────────────────────────────

export function startHandTrackingDaemon(
  onGesture: (result: HandDetectionResult) => void,
  intervalMs = 200
): { stop: () => void } {
  const tmpDir = '/tmp/devin_holomat';
  if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir, { recursive: true });
  const framePath = path.join(tmpDir, 'frame.jpg');

  const captureScript = `
import cv2, time, os
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("NO_CAMERA")
    exit(1)
while True:
    ret, frame = cap.read()
    if ret:
        cv2.imwrite("${framePath}", frame)
    time.sleep(${intervalMs / 1000})
`;

  const captureChild = cp.spawn('python3', ['-c', captureScript], {
    env: { ...process.env, DISPLAY: ':0' },
  });

  const timer = setInterval(async () => {
    if (fs.existsSync(framePath)) {
      const result = await detectHandGesture(framePath);
      if (result.detected) onGesture(result);
    }
  }, intervalMs);

  return {
    stop: () => {
      clearInterval(timer);
      captureChild.kill();
    },
  };
}

// ── Screen projection mapping (Holomat perspective calibration) ───────────────

export interface ProjectionCalibration {
  corners: TransformPoint[];
  width: number;
  height: number;
  calibrated: boolean;
}

const calibrationFile = path.join(DEVIN_ROOT, 'config', 'holomat_calibration.json');

export function saveCalibration(cal: ProjectionCalibration): void {
  fs.mkdirSync(path.dirname(calibrationFile), { recursive: true });
  fs.writeFileSync(calibrationFile, JSON.stringify(cal, null, 2), 'utf8');
}

export function loadCalibration(): ProjectionCalibration | null {
  if (!fs.existsSync(calibrationFile)) return null;
  try {
    return JSON.parse(fs.readFileSync(calibrationFile, 'utf8'));
  } catch {
    return null;
  }
}
