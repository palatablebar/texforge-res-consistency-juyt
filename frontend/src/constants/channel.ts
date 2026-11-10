export enum TextureChannel {
  BASE_COLOR = 'base_color',
  NORMAL = 'normal',
  ROUGHNESS = 'roughness',
  METALLIC = 'metallic',
  AO = 'ao',
  HEIGHT = 'height',
}

export const CHANNEL_ORDER: TextureChannel[] = [
  TextureChannel.BASE_COLOR,
  TextureChannel.NORMAL,
  TextureChannel.ROUGHNESS,
  TextureChannel.METALLIC,
  TextureChannel.AO,
  TextureChannel.HEIGHT,
]

export const CHANNEL_LABELS: Record<TextureChannel, string> = {
  [TextureChannel.BASE_COLOR]: '基础色',
  [TextureChannel.NORMAL]: '法线',
  [TextureChannel.ROUGHNESS]: '粗糙度',
  [TextureChannel.METALLIC]: '金属度',
  [TextureChannel.AO]: '环境遮蔽',
  [TextureChannel.HEIGHT]: '高度',
}

export const PACK_PRESETS: Record<string, Partial<Record<'r' | 'g' | 'b' | 'a', TextureChannel>>> = {
  orm: {
    r: TextureChannel.ROUGHNESS,
    g: TextureChannel.METALLIC,
    b: TextureChannel.AO,
    a: TextureChannel.HEIGHT,
  },
  mra: {
    r: TextureChannel.METALLIC,
    g: TextureChannel.ROUGHNESS,
    b: TextureChannel.AO,
    a: TextureChannel.HEIGHT,
  },
}
