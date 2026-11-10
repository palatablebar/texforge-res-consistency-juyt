export enum BlendMode {
  NORMAL = 'normal',
  ADD = 'add',
  MULTIPLY = 'multiply',
  OVERLAY = 'overlay',
  SCREEN = 'screen',
}

export const BLEND_LABELS: Record<BlendMode, string> = {
  [BlendMode.NORMAL]: '正常',
  [BlendMode.ADD]: '相加',
  [BlendMode.MULTIPLY]: '正片叠底',
  [BlendMode.OVERLAY]: '叠加',
  [BlendMode.SCREEN]: '滤色',
}
