/**
 * Malolos FareWatch - Interactive Client Scripts
 * Bayesian Tricycle Fare Deviation Monitoring System
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Sidebar Drawer Toggle (Mobile & Tablet)
  const hamburgerBtn = document.getElementById('hamburgerToggle');
  const sidebar = document.getElementById('appSidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  if (hamburgerBtn && sidebar && sidebarOverlay) {
    hamburgerBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      sidebarOverlay.classList.toggle('open');
    });

    sidebarOverlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      sidebarOverlay.classList.remove('open');
    });
  }

  // 2. User Menu Dropdown Toggle
  const userProfileBtn = document.getElementById('userProfileToggle');
  const userDropdownMenu = document.getElementById('userDropdownMenu');

  if (userProfileBtn && userDropdownMenu) {
    userProfileBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdownMenu.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!userDropdownMenu.contains(e.target) && !userProfileBtn.contains(e.target)) {
        userDropdownMenu.classList.remove('show');
      }
    });
  }

  // 3. Photo Evidence Preview in Report Form
  const photoInput = document.getElementById('farePhotoInput');
  const previewBox = document.getElementById('photoPreviewBox');
  const previewImg = document.getElementById('photoPreviewImage');
  const dropzone = document.getElementById('photoDropzone');

  if (photoInput && previewBox && previewImg) {
    photoInput.addEventListener('change', function () {
      const file = this.files[0];
      if (file) {
        if (file.size > 5 * 1024 * 1024) {
          alert("File size exceeds 5MB limit. Please upload a smaller photo.");
          this.value = "";
          previewBox.style.display = "none";
          return;
        }
        const reader = new FileReader();
        reader.onload = function (e) {
          previewImg.src = e.target.result;
          previewBox.style.display = "block";
        };
        reader.readAsDataURL(file);
      } else {
        previewBox.style.display = "none";
      }
    });

    if (dropzone) {
      dropzone.addEventListener('click', () => photoInput.click());
      dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--primary-blue)';
      });
      dropzone.addEventListener('dragleave', () => {
        dropzone.style.borderColor = 'var(--border-color)';
      });
      dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--border-color)';
        if (e.dataTransfer.files.length) {
          photoInput.files = e.dataTransfer.files;
          const event = new Event('change');
          photoInput.dispatchEvent(event);
        }
      });
    }
  }

  // 4. Photo Lightbox Modal
  const photoModal = document.getElementById('photoModalBackdrop');
  const modalImg = document.getElementById('modalImage');
  const modalCaption = document.getElementById('modalCaption');
  const modalCloseBtn = document.getElementById('modalCloseBtn');

  window.openPhotoModal = function (imgSrc, captionText) {
    if (photoModal && modalImg) {
      modalImg.src = imgSrc;
      if (modalCaption) {
        modalCaption.textContent = captionText || "Commuter Fare Evidence Photo";
      }
      photoModal.classList.add('show');
    }
  };

  window.closePhotoModal = function () {
    if (photoModal) {
      photoModal.classList.remove('show');
    }
  };

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', closePhotoModal);
  }

  if (photoModal) {
    photoModal.addEventListener('click', (e) => {
      if (e.target === photoModal) {
        closePhotoModal();
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && photoModal && photoModal.classList.contains('show')) {
      closePhotoModal();
    }
  });
});
