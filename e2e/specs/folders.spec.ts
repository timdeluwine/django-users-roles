import { test, expect } from '@playwright/test';
import { FileManagerPage } from '../pages/FileManagerPage';

test.describe('Управление папками и навигация', () => {
  test.beforeEach(async ({ page }) => {
    const filePage = new FileManagerPage(page);
    await filePage.login('admin', 'password123');
    await filePage.goto();
  });

  test('Создание папки, вход внутрь, создание подпапки и возврат по крошкам', async ({ page }) => {
    const filePage = new FileManagerPage(page);
    const folderName = `folder_${Date.now()}`;
    const subFolderName = `sub_${Date.now()}`;

    await test.step('Создание корневой тестовой папки', async () => {
      await filePage.createFolder(folderName);
      await expect(page.getByTestId(`folder-link-${folderName}`)).toBeVisible();
    });

    await test.step('Переход внутрь созданной папки', async () => {
      await page.getByTestId(`folder-link-${folderName}`).click();
      await expect(filePage.breadcrumbs).toContainText(folderName);
    });

    await test.step('Создание вложенной подпапки', async () => {
      await filePage.createFolder(subFolderName);
      await expect(page.getByTestId(`folder-link-${subFolderName}`)).toBeVisible();
    });

    await test.step('Навигация назад в Корень через хлебные крошки', async () => {
      await page.getByRole('link', { name: 'Корень' }).click();
      await expect(page.getByTestId(`folder-link-${folderName}`)).toBeVisible();
    });

    await test.step('Рекурсивное удаление папки', async () => {
      await filePage.deleteItem(folderName, true);
      await expect(page.getByTestId(`folder-link-${folderName}`)).not.toBeVisible();
    });
  });

  test('Отмена удаления папки в диалоге подтверждения оставляет её в списке', async ({ page }) => {
    const filePage = new FileManagerPage(page);
    const folderName = `keep_${Date.now()}`;

    await test.step('Создание папки', async () => {
      await filePage.createFolder(folderName);
      await expect(page.getByTestId(`folder-link-${folderName}`)).toBeVisible();
    });

    await test.step('Открытие модалки и клик "Отмена"', async () => {
      await filePage.deleteItem(folderName, false);
      await expect(page.getByTestId(`folder-link-${folderName}`)).toBeVisible();
    });

    await test.step('Очистка после теста', async () => {
      await filePage.deleteItem(folderName, true);
      await expect(page.getByTestId(`folder-link-${folderName}`)).not.toBeVisible();
    });
  });

  test('Попытка создать папку с дублирующимся именем выдает понятную ошибку', async ({ page }) => {
    const filePage = new FileManagerPage(page);
    const folderName = `dup_${Date.now()}`;

    await test.step('Первичное создание папки', async () => {
      await filePage.createFolder(folderName);
    });

    await test.step('Повторное создание с тем же именем', async () => {
      await filePage.createFolder(folderName);
      await expect(filePage.flashMessage).toContainText('уже существует');
    });

    await test.step('Очистка после теста', async () => {
      await filePage.deleteItem(folderName, true);
    });
  });
});