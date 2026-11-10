export enum NoiseType {
  VALUE = 'value',
  PERLIN = 'perlin',
  WORLEY = 'worley',
  FBM = 'fbm',
}

export const NOISE_LABELS: Record<NoiseType, string> = {
  [NoiseType.VALUE]: '值噪声',
  [NoiseType.PERLIN]: '柏林噪声',
  [NoiseType.WORLEY]: '沃利噪声',
  [NoiseType.FBM]: '分形叠加',
}
