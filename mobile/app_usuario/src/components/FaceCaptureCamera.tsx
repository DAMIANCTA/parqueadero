import React, { useEffect, useRef, useState } from "react";
import { Modal, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";

import { colors, fonts } from "../theme/theme";

export function FaceCaptureCamera({
  visible,
  onCancel,
  onCaptured,
}: {
  visible: boolean;
  onCancel: () => void;
  onCaptured: (uri: string) => void;
}) {
  const cameraRef = useRef<CameraView>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [capturing, setCapturing] = useState(false);

  useEffect(() => {
    if (visible && permission && !permission.granted && permission.canAskAgain) {
      requestPermission();
    }
  }, [visible, permission]);

  if (!visible) return null;

  const handleCapture = async () => {
    if (!cameraRef.current || capturing) return;
    setCapturing(true);
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.8 });
      if (photo) onCaptured(photo.uri);
    } finally {
      setCapturing(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onCancel}>
      <View style={styles.screen}>
        {permission?.granted ? (
          <>
            <CameraView ref={cameraRef} style={StyleSheet.absoluteFillObject} facing="front" />
            <View style={styles.overlay} pointerEvents="none">
              <View style={styles.oval} />
              <Text style={styles.guideText}>Coloca tu rostro dentro del marco</Text>
              <Text style={styles.guideSubtext}>Mantente quieto y con buena luz. Toca el botón para tomar la foto.</Text>
            </View>
            <View style={styles.controls}>
              <TouchableOpacity style={styles.sideBtn} onPress={onCancel}>
                <Text style={styles.sideBtnText}>Cancelar</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.captureBtn} onPress={handleCapture} disabled={capturing}>
                <View style={styles.captureBtnInner} />
              </TouchableOpacity>
              <View style={styles.sideBtn} />
            </View>
          </>
        ) : (
          <View style={styles.permissionBox}>
            <Text style={styles.guideText}>
              Necesitamos acceso a tu cámara para registrar tu rostro.
            </Text>
            <TouchableOpacity style={styles.sideBtn} onPress={onCancel}>
              <Text style={styles.sideBtnText}>Cerrar</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#000",
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 30,
  },
  oval: {
    width: 240,
    height: 320,
    borderRadius: 120,
    borderWidth: 3,
    borderColor: "rgba(255,255,255,0.85)",
    marginBottom: 24,
  },
  guideText: {
    fontFamily: fonts.extraBold,
    fontSize: 16,
    color: "#fff",
    textAlign: "center",
  },
  guideSubtext: {
    fontFamily: fonts.regular,
    fontSize: 12.5,
    color: "rgba(255,255,255,0.8)",
    textAlign: "center",
    marginTop: 6,
  },
  controls: {
    position: "absolute",
    bottom: 40,
    left: 0,
    right: 0,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 24,
  },
  sideBtn: {
    width: 80,
  },
  sideBtnText: {
    fontFamily: fonts.semiBold,
    fontSize: 14,
    color: "#fff",
  },
  captureBtn: {
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 4,
    borderColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
  },
  captureBtnInner: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: "#fff",
  },
  permissionBox: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 20,
    padding: 30,
    backgroundColor: colors.navy,
  },
});
