import {test,expect} from '@playwright/test';
import {predictionButtonState} from '../../src/client_scroll_cues.mjs';
import {openClient,client,action,replaceMonths,screenshot,ensureNoException} from './client.helpers.mjs';

test('CL-B01 função de estado do botão preserva as três legendas',()=>{
  expect(predictionButtonState('Calcular previsão',false)).toBe('idle');
  expect(predictionButtonState('Calcular previsão',true)).toBe('unavailable');
  expect(predictionButtonState('Calculando',true)).toBe('running');
  expect(predictionButtonState('Recalcular previsão',false)).toBe('complete');
  expect(predictionButtonState('Recalcular previsão',true)).toBe('unavailable');
  expect(predictionButtonState('Tentar novamente',false)).toBe('retry');
  expect(predictionButtonState('Tentar novamente',true)).toBe('unavailable');
});

test('CL-B02 estados cromáticos, reticências, retorno ao branco e movimento reduzido',
  async({page},info)=>{
    await openClient(page,{width:1024,height:768});
    const button=action(page);
    await expect(button).toHaveCSS('font-size','14px');
    const text=button.locator('p');
    await expect(text).toHaveCSS('font-size','14px');
    // Estados transitórios são reproduzidos na camada DOM; evita treinar o
    // algoritmo duas vezes apenas para testar cor e transição CSS.
    await button.evaluate(el=>{el.disabled=false;});
    await expect(button).toHaveCSS('background-color','rgb(245, 245, 245)');
    await button.hover();
    await expect(button).toHaveCSS('background-color','rgb(216, 216, 216)');
    await button.evaluate(el=>{el.querySelector('p').textContent='Calculando';el.disabled=true;});
    await expect(button).toHaveAttribute('data-n3-prediction-state','running');
    await expect(button).toHaveCSS('background-color','rgb(85, 88, 93)');
    await expect(button).toHaveCSS('color','rgb(245, 245, 245)');
    await expect(button).toBeDisabled();
    await expect(client(page)).toHaveAttribute('data-n3-interaction-locked','true');
    await expect(client(page)).toHaveJSProperty('inert',true);
    await expect(client(page)).toHaveAttribute('aria-busy','true');
    await expect.poll(()=>client(page).evaluate(el=>
      getComputedStyle(el,'::after').backgroundColor)).toBe('rgba(0, 0, 0, 0.48)');
    await expect.poll(async()=>text.evaluate(el=>
      getComputedStyle(el,'::after').animationName)).toBe('n3-calculating-ellipsis');
    const original=await text.evaluate(el=>getComputedStyle(el,'::after').content);
    await expect.poll(async()=>text.evaluate(el=>
      getComputedStyle(el,'::after').content),{timeout:2500,intervals:[180,180,180,180]})
      .not.toBe(original);
    await screenshot(page,info,'CL-B02-executando');
    await page.emulateMedia({reducedMotion:'reduce'});
    await expect.poll(async()=>text.evaluate(el=>
      getComputedStyle(el,'::after').animationName)).toBe('none');
    await expect.poll(async()=>text.evaluate(el=>
      getComputedStyle(el,'::after').content)).toBe('"..."');
    await page.emulateMedia({reducedMotion:'no-preference'});

    await button.evaluate(el=>{
      el.querySelector('p').textContent='Recalcular previsão';el.disabled=false;
    });
    await expect(button).toHaveAttribute('data-n3-prediction-state','complete');
    await expect(button).toHaveAttribute('data-n3-hover-ready','false');
    await expect(button).toHaveCSS('background-color','rgb(245, 245, 245)');
    await expect(button).toBeEnabled();
    await expect(client(page)).not.toHaveAttribute('data-n3-interaction-locked','true');
    await expect(client(page)).toHaveJSProperty('inert',false);
    await screenshot(page,info,'CL-B02-recalcular');
    await page.mouse.move(0,0);
    await button.hover();
    await expect(button).toHaveCSS('background-color','rgb(216, 216, 216)');
    await page.mouse.move(0,0);
    await expect(button).toHaveCSS('background-color','rgb(245, 245, 245)');
    // A supressão deve valer apenas enquanto o ponteiro não tiver saído.
    // Se estiver fora durante a conclusão, o próximo hover funciona normalmente.
    await button.evaluate(el=>{
      el.querySelector('p').textContent='Calculando';el.disabled=true;
    });
    await expect(button).toHaveAttribute('data-n3-prediction-state','running');
    await page.mouse.move(0,0);
    await button.evaluate(el=>{
      el.querySelector('p').textContent='Recalcular previsão';el.disabled=false;
    });
    await expect(button).toHaveAttribute('data-n3-prediction-state','complete');
    await expect(button).toHaveAttribute('data-n3-hover-ready','true');
    await button.hover();
    await expect(button).toHaveCSS('background-color','rgb(216, 216, 216)');
  });

test('CL-B03 integração real: cálculo, conclusão, legenda e dados alterados',
  async({page},info)=>{
    test.slow();
    await openClient(page,{width:1024,height:768});
    const button=action(page);
    if(await button.isDisabled()){
      test.skip(true,'Requer CSV original em data/raw para executar a otimização genética.');
    }
    await expect(button).toHaveText('Calcular previsão');
    await button.click();
    await expect(button).toBeDisabled();
    await expect(page.locator('.churn-workspace-heading[data-run-state="running"]'))
      .toBeVisible({timeout:30000});
    await expect(button).toContainText('Calculando');
    await expect(client(page)).toHaveAttribute('data-n3-interaction-locked','true');
    await expect(client(page)).toHaveJSProperty('inert',true);
    // Mesmo com clique e digitação durante o treino, o formulário não muda
    // e nenhuma atualização interrompe a execução genética em andamento.
    const charge = page.locator('input[aria-label="Cobrança mensal"]');
    const originalCharge = await charge.inputValue();
    const bounds = await charge.boundingBox();
    expect(bounds).toBeTruthy();
    await page.mouse.click(bounds.x + bounds.width / 2, bounds.y + bounds.height / 2);
    await page.keyboard.press('ControlOrMeta+A');
    await page.keyboard.type('175');
    await expect(charge).toHaveValue(originalCharge);
    await expect(charge).not.toBeFocused();
    await screenshot(page,info,'CL-B03-processando');
    await expect(page.locator('.churn-workspace-heading[data-run-state="complete"]'))
      .toBeVisible({timeout:600000});
    await expect(button).toBeEnabled();
    await expect(button).toContainText('Recalcular previsão');
    await expect(client(page)).toHaveJSProperty('inert',false);
    await expect(client(page)).not.toHaveAttribute('data-n3-interaction-locked','true');
    await expect(button).toHaveCSS('background-color','rgb(245, 245, 245)');
    await expect(page.locator('.churn-comparison .churn-model')).toHaveCount(2);
    await expect(page.locator('.n3-status .n3-status-title')).toHaveText('Cancelamento previsto');
    await expect(page.locator('.n3-status .n3-subset-count')).toHaveText('121');
    await expect(page.locator('.n3-status .n3-feature-count')).toHaveText('9/19');
    await expect(page.locator('.n3-status [role="progressbar"]')).toHaveAttribute('aria-valuenow','15');
    await expect(page.locator('.n3-risk-fill')).toHaveCount(2);
    await expect(page.locator('.n3-risk-threshold')).toHaveCount(2);
    await expect(page.locator('.n3-f1-line')).toHaveCount(1);
    await expect(page.locator('.n3-fitness-line')).toHaveCount(1);
    await expect(page.locator('.n3-chart-point')).toHaveCount(15);
    await expect(page.locator('.churn-bit')).toHaveCount(19);
    await expect(page.locator('.churn-bit.is-on')).toHaveCount(9);
    await expect(page.locator('.n3-impact')).toContainText('+8');
    await expect(page.locator('.churn-run-check')).toBeVisible();
    await screenshot(page,info,'CL-B03-concluido');

    await replaceMonths(page,4);
    await expect(page.locator('.churn-workspace-heading[data-run-state="stale"]'))
      .toBeVisible();
    await expect(page.locator('.churn-comparison .churn-state'))
      .toHaveText('Dados alterados');
    await expect(page.locator('.n3-risk-fill')).toHaveCount(0);
    await expect(page.locator('.churn-chromosome')).toContainText('Subconjunto anterior');
    await expect(page.locator('.churn-chart')).toContainText('execução anterior');
    await expect(page.locator('.n3-impact')).toContainText('execução anterior');
    await expect(page.locator('.n3-status .n3-status-title')).toHaveText('Dados alterados');
    await expect(button).toContainText('Recalcular previsão');
    await expect(button).toBeEnabled();
    await ensureNoException(page);
    await screenshot(page,info,'CL-B03-dados-alterados');
  });
