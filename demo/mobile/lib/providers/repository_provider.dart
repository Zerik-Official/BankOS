import 'package:bankos_mobile/core/config/api_config.dart';
import 'package:bankos_mobile/data/api/api_bank_repository.dart';
import 'package:bankos_mobile/data/api/api_client.dart';
import 'package:bankos_mobile/data/bank_repository.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Provides the data source used by the whole app: the real backend API.
///
/// Tests replace it with `FakeBankRepository` using `overrideWithValue`.
final Provider<BankRepository> bankRepositoryProvider =
    Provider<BankRepository>((Ref ref) {
      return ApiBankRepository(client: ApiClient(baseUrl: ApiConfig.baseUrl));
    });
