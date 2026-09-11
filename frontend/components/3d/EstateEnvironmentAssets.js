import React, { Suspense, useMemo } from 'react';
import { Box3, Vector3 } from 'three';
import { useGLTF } from '@react-three/drei';

const ASSET_ROOT = '/assets/kenney/nature-kit/Models/GLTF%20format';

const finiteNumber = (value, fallback = 0) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
};

const normalizePosition = (position) => {
  const value = Array.isArray(position) ? position : [0, 0, 0];
  return [0, 1, 2].map((index) => finiteNumber(value[index], 0));
};

function NatureAsset({ file, position, rotation = [0, 0, 0], targetHeight = 2, scale = 1 }) {
  const { scene } = useGLTF(`${ASSET_ROOT}/${file}.glb`);
  const model = useMemo(() => {
    const clone = scene.clone(true);
    clone.traverse((object) => {
      const attribute = object.geometry?.attributes?.position;
      if (!attribute) return;

      for (let index = 0; index < attribute.array.length; index += 1) {
        attribute.array[index] = finiteNumber(attribute.array[index], 0);
      }
      attribute.needsUpdate = true;
      object.geometry.computeBoundingBox();
      object.geometry.computeBoundingSphere();
    });

    const bounds = new Box3().setFromObject(clone);
    const size = bounds.getSize(new Vector3());
    const height = Math.max(finiteNumber(size.y, 1), 1);
    clone.scale.setScalar((finiteNumber(targetHeight, 2) / height) * finiteNumber(scale, 1));
    const scaledBounds = new Box3().setFromObject(clone);
    const center = scaledBounds.getCenter(new Vector3());
    clone.position.set(-finiteNumber(center.x), -finiteNumber(scaledBounds.min.y), -finiteNumber(center.z));
    return clone;
  }, [scene, targetHeight, scale]);

  return <primitive object={model} position={normalizePosition(position)} rotation={rotation} castShadow receiveShadow />;
}

const landscapeAssets = [
  ['tree_oak', [-27, 0, -24], 7, 1],
  ['tree_default', [-21, 0, 25], 6, 1],
  ['tree_pineTallA', [26, 0, -22], 8, 1],
  ['tree_pineRoundC', [29, 0, 22], 6, 1],
  ['tree_fat', [-30, 0, 5], 5, 1],
  ['tree_tall', [30, 0, 5], 7, 1],
  ['plant_bushLarge', [-17, 0, -18], 2, 1],
  ['plant_bushDetailed', [18, 0, -18], 2, 1],
  ['rock_largeA', [-24, 0, 17], 2.5, 1],
  ['rock_largeC', [23, 0, 16], 2.2, 1],
  ['flower_yellowA', [-13, 0, -16], 1.2, 1],
  ['flower_redB', [14, 0, -16], 1.2, 1],
  ['crops_cornStageC', [-12, 0, -11], 1.8, 1],
  ['crops_cornStageC', [-8, 0, -11], 1.8, 1],
  ['crops_wheatStageB', [9, 0, -11], 1.8, 1],
  ['crops_wheatStageB', [13, 0, -11], 1.8, 1],
  ['fence_simple', [-18, 0, -12], 1.6, 1],
  ['fence_simple', [18, 0, -12], 1.6, 1],
  ['ground_pathStraight', [0, 0, 18], 0.25, 2],
];

export default function EstateEnvironmentAssets() {
  return (
    <group>
      {landscapeAssets.map(([file, position, targetHeight, scale], index) => (
        <Suspense fallback={null} key={`${file}-${index}`}>
          <NatureAsset file={file} position={position} targetHeight={targetHeight} scale={scale} />
        </Suspense>
      ))}
    </group>
  );
}
