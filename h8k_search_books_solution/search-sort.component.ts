import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { IBook } from '../books/books.component';

type SortOrder = 'asc' | 'desc' | null;

@Component({
  selector: 'app-search-sort',
  templateUrl: './search-sort.component.html',
  styleUrls: ['./search-sort.component.scss'],
  standalone: false,
})
export class SearchSortComponent implements OnInit, OnChanges {
  @Input() booksList: IBook[] = [];

  /** Books currently shown (filtered + sorted). */
  displayedBooks: IBook[] = [];

  private searchTerm = '';
  private sortOrder: SortOrder = null;

  ngOnInit(): void {
    this.refreshDisplayedBooks();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['booksList']) {
      this.refreshDisplayedBooks();
    }
  }

  onSearchInput(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchTerm = value;
    this.refreshDisplayedBooks();
  }

  sortAsc(): void {
    this.sortOrder = 'asc';
    this.refreshDisplayedBooks();
  }

  sortDesc(): void {
    this.sortOrder = 'desc';
    this.refreshDisplayedBooks();
  }

  private refreshDisplayedBooks(): void {
    const source = this.booksList ?? [];
    const q = this.searchTerm.trim().toLowerCase();

    let next = q.length
      ? source.filter((b) => (b.genre ?? '').toLowerCase().includes(q))
      : [...source];

    if (this.sortOrder === 'asc') {
      next = [...next].sort((a, b) =>
        (a.book_name ?? '').localeCompare(b.book_name ?? '', undefined, {
          sensitivity: 'base',
        }),
      );
    } else if (this.sortOrder === 'desc') {
      next = [...next].sort((a, b) =>
        (b.book_name ?? '').localeCompare(a.book_name ?? '', undefined, {
          sensitivity: 'base',
        }),
      );
    }

    this.displayedBooks = next;
  }
}
