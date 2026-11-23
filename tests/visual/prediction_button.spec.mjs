import { test, expect } from '@playwright/test';
import { predictionButtonState } from '../../src/client_scroll_cues.mjs';

test('estados do botão derivam da legenda original do Streamlit', () => {
  expect(predictionButtonState('Calcular previsão',false)).toBe('idle');
  expect(predictionButtonState('Calcular previsão',true)).toBe('unavailable');
  expect(predictionButtonState('Calculando',true)).toBe('running');
  expect(predictionButtonState('Calculando...',true)).toBe('running');
  expect(predictionButtonState('Recalcular previsão',false)).toBe('complete');
});

test('anima reticências e restaura branco quando o cálculo termina sob o cursor', async ({page}) => {
  await page.setViewportSize({width:1024,height:768});
  await page.goto('/', {waitUntil:'domcontentloaded'});
  const button=page.locator('.st-key-dashboard-client-footer [data-testid="stButton"] button');
  await expect(button).toBeVisible();
  // Simular apenas os estados visuais, sem lançar uma busca genética real:
  // a suíte principal verifica a execução completa dos modelos.
  await button.evaluate(el => {el.disabled=false;});
  await button.hover();
  await expect(button).toHaveCSS('background-color','rgb(216, 216, 216)');

  await button.evaluate(el => {
    el.querySelector('p').textContent='Calculando';
    el.disabled=true;
  });
  await expect(button).toHaveAttribute('data-n3-prediction-state','running');
  await expect(button).toHaveCSS('background-color','rgb(85, 88, 93)');
  await expect(button).toHaveCSS('color','rgb(245, 245, 245)');
  const text=button.locator('p');
  await expect.poll(() => text.evaluate(el =>
    getComputedStyle(el,'::after').animationName)).toBe('n3-calculating-ellipsis');
  const initial=await text.evaluate(el => getComputedStyle(el,'::after').content);
  await expect.poll(() => text.evaluate(el => getComputedStyle(el,'::after').content), {
    timeout:2500,intervals:[150,150,150,150,150,150,150],
  }).not.toBe(initial);

  // Respeitar o sistema operacional: com movimento reduzido, três pontos fixos.
  await page.emulateMedia({reducedMotion:'reduce'});
  await expect.poll(() => text.evaluate(el =>
    getComputedStyle(el,'::after').animationName)).toBe('none');
  await expect.poll(() => text.evaluate(el =>
    getComputedStyle(el,'::after').content)).toBe('"..."');
  await page.emulateMedia({reducedMotion:'no-preference'});

  // O ponteiro não sai do botão, portanto um :hover convencional ainda
  // estaria ativo. O observador deve desarmá-lo após a conclusão.
  await button.evaluate(el => {
    el.querySelector('p').textContent='Recalcular previsão';
    el.disabled=false;
  });
  await expect(button).toHaveAttribute('data-n3-prediction-state','complete');
  await expect(button).toHaveAttribute('data-n3-hover-ready','false');
  await expect(button).toHaveCSS('background-color','rgb(245, 245, 245)');
  await page.mouse.move(0,0);
  await button.hover();
  await expect(button).toHaveCSS('background-color','rgb(216, 216, 216)');
  await page.mouse.move(0,0);
  await expect(button).toHaveCSS('background-color','rgb(245, 245, 245)');
});
