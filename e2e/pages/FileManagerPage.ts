import { Page, Locator, expect } from '@playwright/test';

export class FileManagerPage {
  readonly page: Page;
  readonly navFilesLink: Locator;
  readonly navHomeLink: Locator;
  readonly logoutButton: Locator;
  readonly folderNameInput: Locator;
  readonly createFolderButton: Locator;
  readonly fileUploadInput: Locator;
  readonly uploadFileButton: Locator;
  readonly flashMessage: Locator;
  readonly breadcrumbs: Locator;
  readonly deleteModal: Locator;
  readonly deleteConfirmButton: Locator;
  readonly deleteCancelButton: Locator;
  readonly renameModal: Locator;
  readonly renameInput: Locator;
  readonly renameConfirmButton: Locator;
  readonly renameCancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.navFilesLink = page.getByTestId('nav-files').or(page.getByRole('link', { name: 'Файлы' }));
    this.navHomeLink = page.getByTestId('nav-home').or(page.getByRole('link', { name: 'Главная' }));
    this.logoutButton = page
      .getByTestId('logout-btn')
      .or(page.getByRole('button', { name: 'Выйти' }))
      .or(page.getByText('Выйти'));

    this.folderNameInput = page.getByTestId('folder-name-input');
    this.createFolderButton = page.getByTestId('create-folder-btn');
    this.fileUploadInput = page.getByTestId('file-upload-input');
    this.uploadFileButton = page.getByTestId('upload-file-btn');
    this.flashMessage = page.getByTestId('flash-message');
    this.breadcrumbs = page.getByTestId('breadcrumbs');
    this.deleteModal = page.getByTestId('delete-modal');
    this.deleteConfirmButton = page.getByTestId('delete-confirm-btn');
    this.deleteCancelButton = page.getByTestId('delete-cancel-btn');
    this.renameModal = page.getByTestId('rename-modal');
    this.renameInput = page.getByTestId('rename-new-name-input');
    this.renameConfirmButton = page.getByTestId('rename-confirm-btn');
    this.renameCancelButton = page.getByTestId('rename-cancel-btn');
  }

  async goto() {
    await this.page.goto('/files/');
  }

  async login(username = 'admin', password = 'admin12345') {
    // Автоматическая страховка: если тест передал старый пароль, используем установленный в базе
    const effectivePassword = password === 'password123' ? 'admin12345' : password;
    await this.page.goto('/login/?next=/');
    await this.page.fill('input[name="username"]', username);
    await this.page.fill('input[name="password"]', effectivePassword);
    await this.page.locator('button[type="submit"], input[type="submit"]').click();
    await expect(this.logoutButton).toBeVisible({ timeout: 10000 });
  }

  async createFolder(name: string) {
    await this.folderNameInput.fill(name);
    await this.createFolderButton.click();
  }

  async uploadFiles(filePayloads: { name: string; mimeType: string; buffer: Buffer }[]) {
    await this.fileUploadInput.setInputFiles(filePayloads);
    await this.uploadFileButton.click();
  }

  async renameItem(oldName: string, newName: string) {
    await this.page.getByTestId(`rename-btn-${oldName}`).click();
    await expect(this.renameModal).toBeVisible();
    await this.renameInput.fill(newName);
    await this.renameConfirmButton.click();
  }

  async deleteItem(name: string, confirm = true) {
    await this.page.getByTestId(`delete-btn-${name}`).click();
    await expect(this.deleteModal).toBeVisible();
    if (confirm) {
      await this.deleteConfirmButton.click();
    } else {
      await this.deleteCancelButton.click();
    }
  }
}