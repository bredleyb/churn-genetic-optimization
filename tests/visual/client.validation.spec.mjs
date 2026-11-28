import {test, expect} from '@playwright/test';
import {openClient, footer, fieldGroup, ensureNoException} from './client.helpers.mjs';

// Os widgets reais impedem valores inválidos; esta fixture injeta somente
// o contrato HTML de feedback emitido pelo Python, para testar o observador
// no DOM real. Não simula treinamento nem muda dados do cliente.
test('CL-V01 feedback realça campo e só move foco ao solicitar correção', async({page})=>{
  await openClient(page,{width:1024,height:768});
  const charge=page.locator('input[aria-label="Cobrança mensal"]');
  const contract=page.getByRole('combobox',{name:'Tipo de contrato',exact:true});
  await contract.focus();
  await footer(page).evaluate(el=>{
    const wrapper=document.createElement('div');
    wrapper.className='n3-client-validation';
    wrapper.innerHTML='<a class="n3-validation-jump" href="#n3-client-validation">Corrigir</a>'+
      '<span hidden id="n3-validation-MonthlyCharges" data-n3-error-label="Cobrança mensal" data-n3-error-tab="">Valor inválido</span>';
    el.append(wrapper);
  });
  await expect(charge).toHaveAttribute('aria-invalid','true');
  await expect(charge).toHaveAttribute('aria-describedby',/n3-validation-MonthlyCharges/);
  const group=page.locator('[data-testid="stNumberInput"]').filter({has:charge});
  await expect(group).toHaveAttribute('data-n3-invalid','true');
  await expect(group.locator('[data-testid="stNumberInputContainer"]').first())
    .toHaveCSS('border-top-color','rgb(121, 169, 245)');
  await expect(contract).toBeFocused();
  await page.getByRole('link',{name:'Corrigir',exact:true}).click();
  await expect(charge).toBeFocused();
  await page.locator('.n3-client-validation').evaluate(el=>el.remove());
  await expect(group).not.toHaveAttribute('data-n3-invalid','true');
  await expect(charge).not.toHaveAttribute('aria-invalid','true');
  await ensureNoException(page);
});
