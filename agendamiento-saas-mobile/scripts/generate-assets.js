#!/usr/bin/env node
/**
 * Genera todos los assets de marca de la app a partir del isotipo y el logo
 * descargados en `assets/brand/`.
 *
 * Outputs (en `assets/`):
 *   icon.png                          1024×1024  Icon iOS (cuadrado, fondo blanco, sin alpha)
 *   adaptive-icon.png                 1024×1024  Android adaptive foreground (con safe zone)
 *   android-icon-foreground.png       1024×1024  Igual que adaptive-icon (legacy + nuevo)
 *   android-icon-background.png       1024×1024  Fondo sólido blanco
 *   android-icon-monochrome.png       1024×1024  Versión monocromática para themed icons
 *   splash-icon.png                   1024×1024  Logo del splash (con padding)
 *   favicon.png                       48×48      Web favicon
 *
 * Uso:
 *   node scripts/generate-assets.js
 */
const path = require('path');
const fs = require('fs');
const sharp = require('sharp');

const ROOT = path.resolve(__dirname, '..');
const SRC_ISOTIPO = path.join(ROOT, 'assets/brand/isotipo.png');
const SRC_LOGO = path.join(ROOT, 'assets/brand/logo.png');
const OUT = path.join(ROOT, 'assets');

const WHITE = { r: 255, g: 255, b: 255, alpha: 1 };

// Paleta de marca — azul NexoSoftDev (lo que se ve en el isotipo)
const BRAND_NAVY = '#0F1F3D';

async function ensureSourcesExist() {
  for (const file of [SRC_ISOTIPO, SRC_LOGO]) {
    if (!fs.existsSync(file)) {
      console.error(`✗ Falta el archivo fuente: ${file}`);
      process.exit(1);
    }
  }
}

/**
 * Carga el isotipo, lo recorta a su contenido real (trim de bordes blancos) y lo
 * devuelve como buffer cuadrado del tamaño pedido, con padding interno opcional.
 *
 * @param {number} canvasSize  tamaño final del cuadrado de salida
 * @param {number} contentRatio  qué % del canvas ocupa el isotipo (0..1)
 * @param {string} bgColor  color del fondo (CSS hex)
 */
async function makeSquareIcon(canvasSize, contentRatio, bgColor = '#FFFFFF') {
  const innerSize = Math.round(canvasSize * contentRatio);

  // Recortar bordes blancos del isotipo original para que el padding sea consistente
  const trimmed = await sharp(SRC_ISOTIPO).trim().toBuffer();
  const resized = await sharp(trimmed)
    .resize(innerSize, innerSize, {
      fit: 'contain',
      background: bgColor,
    })
    .toBuffer();

  // Componer sobre canvas del color de fondo
  const offset = Math.round((canvasSize - innerSize) / 2);
  return sharp({
    create: {
      width: canvasSize,
      height: canvasSize,
      channels: 4,
      background: bgColor,
    },
  })
    .composite([{ input: resized, top: offset, left: offset }])
    .flatten({ background: bgColor })  // quita alpha — iOS lo exige
    .png()
    .toBuffer();
}

async function writeMonochromeIcon(outPath, canvasSize) {
  // Themed icons de Android requieren un PNG en escala de grises, con alpha,
  // donde el contenido es BLANCO sobre transparente. El sistema lo pinta del
  // color de tema del usuario en runtime.
  const trimmed = await sharp(SRC_ISOTIPO).trim().toBuffer();
  const innerSize = Math.round(canvasSize * 0.55);
  const offset = Math.round((canvasSize - innerSize) / 2);

  // Binarizar: lo oscuro del isotipo se vuelve OPACO BLANCO, el resto transparente.
  const binarized = await sharp(trimmed)
    .resize(innerSize, innerSize, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .greyscale()
    .threshold(180)        // < 180 → negro (será luego nuestro blanco opaco)
    .negate({ alpha: false })  // negro ↔ blanco
    .ensureAlpha()
    .toBuffer();

  // Hacer que los pixeles blancos sean opacos y los negros transparentes.
  const { data, info } = await sharp(binarized)
    .raw()
    .toBuffer({ resolveWithObject: true });
  for (let i = 0; i < data.length; i += 4) {
    const isWhite = data[i] > 200;
    data[i + 3] = isWhite ? 255 : 0;  // alpha
    // forzar canal RGB a blanco puro donde es opaco
    if (isWhite) { data[i] = 255; data[i + 1] = 255; data[i + 2] = 255; }
  }
  const mono = await sharp(data, { raw: { width: info.width, height: info.height, channels: 4 } })
    .png()
    .toBuffer();

  // Componer sobre canvas transparente del tamaño final
  return sharp({
    create: {
      width: canvasSize,
      height: canvasSize,
      channels: 4,
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    },
  })
    .composite([{ input: mono, top: offset, left: offset }])
    .png()
    .toFile(outPath);
}

async function main() {
  await ensureSourcesExist();

  console.log('Generando icon.png (iOS, 1024×1024, fondo blanco, sin alpha)...');
  fs.writeFileSync(
    path.join(OUT, 'icon.png'),
    await makeSquareIcon(1024, 0.65, '#FFFFFF'),
  );

  console.log('Generando adaptive-icon.png (Android, foreground con safe zone)...');
  // Android recorta el icon a círculo/squircle. El isotipo debe quedar en el
  // 66% central para que NUNCA se recorte. Fondo transparente para que el
  // background layer lo provea.
  const trimmed = await sharp(SRC_ISOTIPO).trim().toBuffer();
  const foregroundInner = await sharp(trimmed)
    .resize(640, 640, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .toBuffer();
  await sharp({
    create: { width: 1024, height: 1024, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } },
  })
    .composite([{ input: foregroundInner, top: 192, left: 192 }])
    .png()
    .toFile(path.join(OUT, 'adaptive-icon.png'));

  console.log('Generando android-icon-foreground.png...');
  // Copia: en Expo SDK 56 el campo es `foregroundImage`.
  fs.copyFileSync(
    path.join(OUT, 'adaptive-icon.png'),
    path.join(OUT, 'android-icon-foreground.png'),
  );

  console.log('Generando android-icon-background.png (blanco sólido)...');
  await sharp({
    create: { width: 1024, height: 1024, channels: 3, background: WHITE },
  })
    .png()
    .toFile(path.join(OUT, 'android-icon-background.png'));

  console.log('Generando android-icon-monochrome.png (themed icons)...');
  await writeMonochromeIcon(path.join(OUT, 'android-icon-monochrome.png'), 1024);

  console.log('Generando splash-icon.png (con padding generoso)...');
  fs.writeFileSync(
    path.join(OUT, 'splash-icon.png'),
    await makeSquareIcon(1024, 0.45, '#FFFFFF'),
  );

  console.log('Generando favicon.png (48×48)...');
  fs.writeFileSync(
    path.join(OUT, 'favicon.png'),
    await makeSquareIcon(48, 0.7, '#FFFFFF'),
  );

  console.log('\n✓ Listo. Assets generados:');
  for (const f of [
    'icon.png',
    'adaptive-icon.png',
    'android-icon-foreground.png',
    'android-icon-background.png',
    'android-icon-monochrome.png',
    'splash-icon.png',
    'favicon.png',
  ]) {
    const stat = fs.statSync(path.join(OUT, f));
    console.log(`  - ${f.padEnd(32)} ${(stat.size / 1024).toFixed(1)} KB`);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
